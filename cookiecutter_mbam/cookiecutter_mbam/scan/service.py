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
from celery import group, chain
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

        self.local_path, self.filename, self.dcm = self._process_file(image_file)

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

        ext, filename, local_path = self._process_filename(image_file.filename)
        image_file.save(local_path)

        if ext == '.nii':
            image_file, local_path, filename = self._compress_file(local_path, filename)

        image_file.close()
        dcm = ext == '.zip'

        return local_path, filename, dcm

    def _process_filename(self, filename):
        """Derive information from the filename

        :param str filename: the name of the file as stored on the image_file object
        :return: a three-tuple of the extension of the file, the basename of the file, and the path to write the file to
        in local storage
        """
        _, ext = os.path.splitext(filename)
        filename = os.path.basename(filename)
        local_path = os.path.join(self.file_depot, filename)
        return ext, filename, local_path

    def _compress_file(self, local_path, filename):
        """Compress a scan

        Gzips the image file and returns data about the gzipped file.

        :param str local_path: the path to the uncompressed file
        :param str filename: the name of the uncompressed file
        :return: a three-tuple of the compressed file, the path to that file, and its name
        :rtype: tuple
        """
        image_file, gz_path = gzip_file(local_path)
        os.remove(local_path)
        local_path = gz_path
        filename = filename + '.gz'
        return image_file, local_path, filename

    def _error_proc(self, status_type=''):

        error_proc = self._error_handler(log_message='generic_message', email_admin=True, email_user=False)

        if len(status_type):
            error_proc = error_proc | self.set_attribute(self.scan.id, status_type, 'Error')

        return error_proc

    def add_to_cloud_storage(self):
        """Construct the celery chain to upload an original scan file to cloud storage

        :return: Celery chain that uploads a scan to cloud storage
        :rtype: celery.canvas.Signature
        """

        return chain(
            self.csc.upload_to_cloud_storage(self.file_depot, self.scan_info, filename=self.filename),
            self.set_attribute(self.scan.id, 'orig_aws_key', passed_val=True),
            self.set_attribute(self.scan.id, 'aws_status', val='Uploaded')
        ).set(link_error=self._error_proc('aws_status'))

    def add_to_xnat_and_run_freesurfer(self, is_first_scan, set_sub_and_exp_attrs, labels):
        """Construct the celery chain that performs XNAT functions

        Constructs the chain to upload a file to XNAT and update user, experiment, and scan representations in the MBAM
        database, and if the file is a dicom, appends to that chain a chain that runs dicom conversion, and finally
        sets the error handler on the chain.

        :param is_first_scan: whether this scan is the first to be uploaded for this experiment
        :type is_first_scan: bool
        :param set_sub_and_exp_attrs: None or the signature of the task to set subject and/or experiment XNAT attributes
        :type set_sub_and_exp_attrs: Union([NoneType, celery.canvas.Signature]
        :param labels:
        :return: Celery chain that performs XNAT functions
        :rtype: celery.canvas.Signature
        """

        if self.dcm:
            xnat_chain = chain(self._upload_file_to_xnat(is_first_scan, set_sub_and_exp_attrs), self._convert_dicom())
        else:
            xnat_chain = self._upload_file_to_xnat(is_first_scan, set_sub_and_exp_attrs)

        xnat_chain = xnat_chain | self._trigger_job(json.dumps(self._run_freesurfer()))

        return xnat_chain.set(link_error=self._error_proc())

    def _run_container(self, process_name, download_suffix, upload_suffix, ds):

        return chain(
            self.get_attribute(self.scan.id, attr='xnat_uri'),
            self.xc.gen_container_data(download_suffix=download_suffix, upload_suffix=upload_suffix),
            self.xc.launch_and_poll_for_completion(process_name),
            ds.update_derivation_model('status', exception_on_failure=True)
        )

    def _download_files_from_xnat(self, local_path, suffix, exclusions=[], single_file=True):

        return chain(
            self.get_attribute(self.scan.id, attr='xnat_uri'),
            self.xc.dl_files_from_xnat(local_path, suffix=suffix, exclusions=exclusions, single_file=single_file),
        )

    # todo: the last piece of this should be deleting the directory from the web server
    def _upload_derivation_to_cloud_storage(self, local_path, filename, ds):
        return chain(
            self.csc.upload_to_cloud_storage(local_path, self.scan_info, filename=filename),
            ds.update_derivation_model('cloud_storage_key')
        )

    def _run_container_retrieve_and_store_files(self, process_name, download_suffix, upload_suffix, filename,
                                                    dl_exclusions=[], single_file=True, zip=False):
        ds = DerivationService([self.scan])
        ds.create(process_name)

        local_path = os.path.join(self.file_depot, str(self.scan.id))

        run_container = self._run_container(process_name, download_suffix, upload_suffix, ds)
        download_files = self._download_files_from_xnat(local_path, upload_suffix,
                                                        exclusions=dl_exclusions, single_file=single_file)
        upload_to_cloud_storage = self._upload_derivation_to_cloud_storage(local_path, filename, ds)

        if zip:
            upload_to_cloud_storage = self.zipdir(path=local_path, name=filename) | upload_to_cloud_storage

        return chain(run_container, download_files, upload_to_cloud_storage)

    def _run_freesurfer(self):

        return self._run_container_retrieve_and_store_files(
            process_name='freesurfer_recon_all',
            download_suffix='/resources/NIFTI/files',
            upload_suffix='/resources/FSv6/files',
            filename='freesurfer.zip',
            single_file=False,
            dl_exclusions={'Name': 'json'}
        )

    def _convert_dicom(self):

        return self._run_container_retrieve_and_store_files(
            process_name='dicom_to_nifti',
            download_suffix='/resources/DICOM/files',
            upload_suffix='/resources/NIFTI/files',
            filename=self.xnat_labels['scan']['xnat_label']
        )

    def _upload_file_to_xnat(self, is_first_scan, set_sub_and_exp_attrs):
        """Construct a Celery chain to upload a file to XNAT

        Constructs a chain that uploads the scan file to XNAT, sets XNAT-relevant attributes of the scan object, and
        gets the scan URI to pass to the dicom conversion chain.

        :param is_first_scan: whether the current scan is the first to be uploaded for the current experiment
        :type is_first_scan: bool
        :param set_sub_and_exp_attrs: either None or the signature of the task that updates subject and/or experiment with their
        XNAT attributes
        :type set_sub_and_exp_attrs: Union([NoneType, celery.canvas.Signature])
        :return: the signature of the chain to upload a file to XNAT
        :rtype: celery.canvas.Signature
        """

        return chain(
            self.xc.upload_scan_file(self.local_path, self.xnat_labels, import_service=self.dcm,
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







