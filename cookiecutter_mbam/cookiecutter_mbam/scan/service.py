# -*- coding: utf-8 -*-
"""Scan service.

This module implements adding a scan to the database, and setting up Celery chains to upload a scan to cloud storage
backup, upload the scan to XNAT, and start the Freesurfer recon process.

Todo: do we want to infer file type from extension?  Or use some other method?

Todo: Right now if we use the import service XNAT is inferring its own scan id.  What do we want to do about that?

Todo: if someone uploads a zip file we don't actually know that there are dicoms inside (could be NIFTI).  Consider this
fact.

Todo: figure out why redis-server not running doesn't get caught as Exception.  Figure out how to catch it.

Todo: consider that the import service leaves a file as a .nii, but upload service leaves a file as .nii.gz.

"""

import json
from pathlib import Path
from celery import chain
from cookiecutter_mbam.config import config_by_name, config_name
from .models import Scan
from cookiecutter_mbam.base.models import BaseService
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.storage import CloudStorageConnection
from cookiecutter_mbam.derivation import DerivationService
from .utils import gzip_file
from cookiecutter_mbam.xnat.tasks import *
from .tasks import set_scan_attribute, get_scan_attribute, set_scan_attributes
import logging

from flask import current_app

logger = logging.getLogger()


def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


tasks = {'set_attribute': set_scan_attribute, 'get_attribute': get_scan_attribute,
         'set_attributes': set_scan_attributes}


class ScanService(BaseService):
    def __init__(self, user, experiment, tasks=tasks):
        super().__init__(Scan)
        self.user = user
        self.experiment = experiment
        self.instance_path = current_app.instance_path[:-8]
        self._config_read()
        self.tasks = tasks
        self.derivation_services = {}

    def _config_read(self):
        """Scan service configuration
        Obtains the configuration with config_by_name, and sets the upload path and creates XNAT Connection and a Cloud
        Storage Connection instance and attaches them to the scan service object.
        :return: None
        """

        config = config_by_name[config_name]
        self.file_depot = os.path.join(self.instance_path, config.files['file_depot'])
        self.xc = XNATConnection(config=config.XNAT)
        self.csc = CloudStorageConnection(config=config.AWS)

    def add_to_database(self, image_file, xnat_labels):
        """Add a scan to the database

        Calls methods to add the scan to the MBAM database, infer file type, add scan level XNAT id to the XNAT labels
        dictionary, and set the scan_info attribute

        :param image_file: the file object
        :type image_file: werkzeug.datastructures.FileStorage
        :param xnat_labels: the XNAT labels for the subject and experiment the scan belongs to
        :type xnat_labels: dict
        :return: None
        """

        self.scan = self._add_scan_to_database()

        self._process_file(image_file)

        self._update_xnat_labels(xnat_labels)

        self.scan_info = [self.user.id, self.experiment.id, self.scan.id]

    def _update_xnat_labels(self, xnat_labels):
        """Add scan level xnat id to the xnat_labels dictionary

        :param xnat_labels: the XNAT labels for the subject and experiment the scan belongs to
        :type xnat_labels: dict
        :return: None
        """

        scan_level_xnat_labels = self.xc.scan_labels(self.experiment, dcm=self.dcm)
        xnat_labels.update(scan_level_xnat_labels)
        self.xnat_labels = xnat_labels

    def _process_file(self, image_file):
        """Prepare file for upload to XNAT and cloud storage

        :param image_file: the file object
        :type image_file: werkzeug.datastructures.FileStorage
        :return: three-tuple of the path to the file on local disk, the name of the file and a boolean indicating if the
        file is a zip file
        :rtype: tuple
        """

        self.ext, self.orig_filename = self._process_filename(image_file.filename)
        self.filename = 'T1' + self.ext
        self.dcm = self.ext == '.zip'

        self._write_local_files(image_file)

    def _process_filename(self, filename):
        """Derive information from the filename

        :param str filename: the name of the file as stored on the image_file object
        :return: a three-tuple of the extension of the file, the basename of the file, and the path to write the file to
        in local storage
        """

        ext = ''.join(Path(filename).suffixes)
        filename = os.path.basename(filename)
        return ext, filename

    def _write_local_files(self, image_file):

        self.local_dir = os.path.join(self.file_depot, str(self.scan.id))
        if not os.path.isdir(self.local_dir): os.mkdir(self.local_dir)

        for dest in ['cloud', 'xnat']:
            dest_dir = os.path.join(self.local_dir, dest)
            if not os.path.isdir(dest_dir): os.mkdir(dest_dir)
            file_path = os.path.join(dest_dir, self.filename)

            if dest == 'cloud':
                image_file.save(file_path)
                if self.ext == '.nii':
                    image_file, file_path = self._compress_file(file_path)
                    self.filename += '.gz'
            if dest == 'xnat':
                shutil.copy(os.path.join(self.local_dir, 'cloud', self.filename), file_path)

        image_file.close()


    def _compress_file(self, local_path):
        """Compress a scan

        Gzips the image file and returns data about the gzipped file.

        :param str local_path: the path to the uncompressed file
        :param str filename: the name of the uncompressed file
        :return: a two-tuple of the compressed file and the path to that file
        :rtype: tuple
        """
        image_file, gz_path = gzip_file(local_path)
        os.remove(local_path)
        return image_file, gz_path

    def _error_proc(self, status_type=''):

        error_proc = self._error_handler(log_message='generic_message', email_admin=True, email_user=False)

        if len(status_type):
            error_proc = error_proc | self.set_attribute(self.scan.id, status_type, 'Error')

        return error_proc

    def add_to_cloud_storage(self):
        """Construct the celery chain to upload an original scan file to cloud storage

        :return: Celery chain that uploads a scan to cloud storage
        :rtype: celery.canvas._chain
        """

        local_dir = os.path.join(self.local_dir, 'cloud')

        return chain(
            self.csc.upload_to_cloud_storage(local_dir, self.scan_info, filename=self.filename, delete=True),
            self.set_attribute(self.scan.id, 'orig_aws_key', passed_val=True),
            self.set_attribute(self.scan.id, 'aws_status', val='Uploaded')
        ).set(link_error=self._error_proc('aws_status'))

    def add_to_xnat_and_run_freesurfer(self, is_first_scan, set_sub_and_exp_attrs):
        """Construct the celery chain that performs XNAT functions

        Constructs the chain to upload a file to XNAT and update user, experiment, and scan representations in the MBAM
        database, and if the file is a dicom, appends to that chain a chain that runs dicom conversion, and finally
        sets the error handler on the chain.

        :param is_first_scan: whether this scan is the first to be uploaded for this experiment
        :type is_first_scan: bool
        :param set_sub_and_exp_attrs: None or the signature of the task to set subject and/or experiment XNAT attributes
        :type set_sub_and_exp_attrs: Union([NoneType, celery.canvas.Signature]
        :return: Celery chain that performs XNAT functions
        :rtype: celery.canvas._chain
        """

        if self.dcm:
            xnat_chain = chain(self._upload_file_to_xnat(is_first_scan, set_sub_and_exp_attrs), self._convert_dicom())
        else:
            xnat_chain = self._upload_file_to_xnat(is_first_scan, set_sub_and_exp_attrs)

        xnat_chain = xnat_chain | self._trigger_job(json.dumps(self._run_freesurfer()))

        return xnat_chain.set(link_error=self._error_proc())

    def _run_container(self, process_name, download_suffix, upload_suffix, ds):
        """Construct a celery chain to run a container

        Constructs the chain to get the uri of the scan, generate the input data for the container, launch the container
        and poll for completion, and finally update the derivation status when the container is finished.

        :param process_name: identifier for the process
        :type process_name: str
        :param download_suffix: what to append to the scan uri to locate files to download
        :type download_suffix: str
        :param upload_suffix: what to append to the scan uri to locate files to upload
        :type upload_suffix: str
        :param ds: derivation service
        :type ds: cookiecutter_mbam.derivation.service.DerivationService
        :return: the celery chain to run the container
        :rtype: celery.canvas._chain
        """

        return chain(
            self.get_attribute(self.scan.id, attr='xnat_uri'),
            self.xc.gen_container_data(download_suffix=download_suffix, upload_suffix=upload_suffix),
            self.xc.launch_and_poll_for_completion(process_name),
            ds.update_derivation_model('status', exception_on_failure=True)
        )

    def _download_files_from_xnat(self, local_dir, suffix, conditions=[], single_file=True):
        """Construct a celery chain to download files from xnat

        :param local_path: the path on the webserver where the file will be saved
        :param suffix: suffix to attach to xnat uri in order to locate the files to download
        :param conditions: keys to a dictionary of optional conditions to put on whether to download a file
        :type conditions: list
        :param single_file: whether the task will download one file or multiple
        :type single_file: bool
        :return: a celery chain to download files from xnat
        :rtype: celery.canvas._chain
        """

        return chain(
            self.get_attribute(self.scan.id, attr='xnat_uri'),
            self.xc.dl_files_from_xnat(local_dir, suffix=suffix, conditions=conditions, single_file=single_file),
        )

    def _upload_derivation_to_cloud_storage(self, local_path, filename, ds, delete=True):
        """Construct a celery chain to upload a derivation to cloud storage

        :param local_path: the path to the file
        :type local_path: str
        :param filename: the name of the file
        :type filename: str
        :param ds: the derivation service object that updates the derivation model
        :type ds: cookiecutter_mbam.derivation.service.DerivationService
        :param delete: whether to delete the file and its containing directory
        :type delete: bool
        :return: None
        """

        return chain(
            self.csc.upload_to_cloud_storage(local_path, self.scan_info, filename=filename, delete=delete),
            ds.update_derivation_model('cloud_storage_key')
        )


    def _run_container_retrieve_and_store_files(self, process_name, download_suffix, upload_suffix, filename, local_dir,
                                                dl_conditions=[], single_file=True, zip=False, dest_for_zip=''):
        """Construct a celery chain to run an XNAT container, download the output, and back it up to cloud storage

        :param process_name: identifier for the process
        :type process_name: str
        :param download_suffix: what to append to the scan uri to locate files to download
        :type download_suffix: str
        :param upload_suffix: what to append to the scan uri to locate files to upload
        :type upload_suffix: str
        :param filename: the name to use when writing the file
        :type filename: str
        :param dl_conditions: keys to a dictionary of optional conditions to put on whether to download a file
        :type dl_conditions: list
        :param single_file: whether one file will be uploaded or more than one
        :type single_file: bool
        :param zip: whether the downloaded files will need to be zipped before upload
        :return: the celery chain to execute the entire derivation process
        """
        ds = DerivationService([self.scan])
        ds.create(process_name)

        run_container = self._run_container(process_name, download_suffix, upload_suffix, ds)
        download_files = self._download_files_from_xnat(local_dir, upload_suffix, conditions=dl_conditions,
                                                        single_file=single_file)

        if zip: local_dir = dest_for_zip

        upload_to_cloud_storage = self._upload_derivation_to_cloud_storage(local_dir, filename, ds, delete=True)

        if zip: upload_to_cloud_storage = chain(
            self.zipdir(dir_to_zip=local_dir, dest_dir=dest_for_zip, name=filename),
            upload_to_cloud_storage
        )

        return run_container | download_files | upload_to_cloud_storage


    def _run_freesurfer(self):
        """Construct a chain to run freesurfer recon-all

        :return: the celery chain
        :rtype: celery.canvas._chain
        """

        return self._run_container_retrieve_and_store_files(
            process_name='freesurfer_recon_all',
            download_suffix='/resources/NIFTI/files',
            upload_suffix='/resources/FSv6/files',
            filename='freesurfer.zip',
            single_file=False,
            zip=True,
            local_dir=os.path.join(self.local_dir, 'freesurfer'),
            dest_for_zip=self.local_dir
        )

    def _convert_dicom(self):
        """Construct a chain to convert dicom to nifti

        :return: the celery chain
        :rtype: celery.canvas._chain
        """

        return self._run_container_retrieve_and_store_files(
            process_name='dicom_to_nifti',
            download_suffix='/resources/DICOM/files',
            upload_suffix='/resources/NIFTI/files',
            filename='T1.nii.gz',
            dl_conditions=['json_exclusion'],
            local_dir=self.local_dir
        )


    def _upload_file_to_xnat(self, is_first_scan, set_sub_and_exp_attrs):
        """Construct a Celery chain to upload a file to XNAT

        Constructs a chain that uploads the scan file to XNAT, sets XNAT-relevant attributes of the scan object, and
        gets the scan URI to pass to the dicom conversion chain.

        :param is_first_scan: whether the current scan is the first to be uploaded for the current experiment
        :type is_first_scan: bool
        :param set_sub_and_exp_attrs: either None or the signature of the task that updates subject and/or experiment
        with their XNAT attributes
        :type set_sub_and_exp_attrs: Union([NoneType, celery.canvas.Signature])
        :return: the signature of the chain to upload a file to XNAT
        :rtype: celery.canvas._chain
        """

        local_path = os.path.join(self.local_dir, 'xnat', self.filename)

        return chain(
            self.xc.upload_scan_file(local_path, self.xnat_labels, import_service=self.dcm,
                                     is_first_scan=is_first_scan, set_sub_and_exp_attrs=set_sub_and_exp_attrs),
            self.set_attributes(self.scan.id, passed_val=True),
            self.set_attribute(self.scan.id, 'xnat_status', val='Uploaded'),
            self.get_attribute(self.scan.id, attr='xnat_uri')
        ).set(link_error=self._error_proc('xnat_status'))


    def _add_scan_to_database(self, xnat_status='Pending', aws_status='Pending'):
        """Add a scan to the database

        Creates the scan object, adds it to the database, and sets the initial xnat and cloud storage status

        :return: scan
        :rtype: cookiecutter_mbam.scan.models.Scan
        """

        return Scan.create(experiment_id=self.experiment.id, xnat_status=xnat_status, aws_status=aws_status,
                           user_id=self.experiment.user_id)


    def delete(self, scan_id, delete_from_xnat=False):
        # todo: add delete listener
        """ Delete a scan from the database

        Deletes a scan from the database and optionally deletes it from XNAT. Only admins should delete a scan from XNAT.

        :param int scan_id: the database id of the scan to delete
        :param bool delete_from_xnat: whether to delete the scan file from XNAT, default False
        :return: None
        """
        scan = Scan.get_by_id(scan_id)
        if delete_from_xnat:
            self.xc.xnat_delete(scan.xnat_uri)
            self.experiment.update(num_scans=self.experiment.num_scans - 1)
        scan.delete()
