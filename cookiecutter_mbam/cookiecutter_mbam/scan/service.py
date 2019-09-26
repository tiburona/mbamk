# -*- coding: utf-8 -*-
"""Scan service.

This module implements uploading a scan file to XNAT and adding a scan to the database.

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
        """The top level public method for adding a scan

        Calls methods to infer file type and further process the file, generate xnat identifiers and query strings,
        check what XNAT identifiers objects have, add the scan to the database, and finally begin the process of
        uploading the file to external sites.

        :param file_object image_file: the file object
        :return: None

        """
        self.local_path, self.filename, self.dcm = self._process_file(image_file)

        self._update_xnat_labels(xnat_labels)
        # xnat_labels is correct up to here

        self.scan_info = [xnat_labels[level]['xnat_label'] for level in ('subject', 'experiment', 'scan')]

        self.scan = self._add_scan_to_database()

    def _update_xnat_labels(self, xnat_labels):

        scan_level_xnat_labels = self.xc.scan_labels(self.experiment, dcm=self.dcm)
        xnat_labels.update(scan_level_xnat_labels)
        self.xnat_labels = xnat_labels
        from cookiecutter_mbam.mbam_logging import app_logger
        app_logger.error(xnat_labels, extra={'email_admin': False})
        # This logs correctly.

    def _process_file(self, image_file):
        """Prepare file for upload to XNAT and cloud storage

        :param file_object image_file:
        :return: two-tuple of the path to the file on local disk and a boolean indicating if the file is a zip file
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
        :return: the extension of the file, the basename of the file, and the path to write the file to in local storage
        :rtype: tuple
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
        """
        image_file, gz_path = gzip_file(local_path)
        os.remove(local_path)
        local_path = gz_path
        filename = filename + '.gz'
        return image_file, local_path, filename

    def add_to_cloud_storage(self):
        """Construct the celery chain to upload an original scan file to cloud storage

        :return: Celery chain that uploads a scan to cloud storage
        """
        return chain(
            self.csc.upload_to_cloud_storage(self.file_depot, self.scan_info, filename=self.filename),
            self.set_attribute(self.scan.id, 'orig_aws_key', passed_val=True)
        )

    # todo: answer question about whether you can have separate error procs on two sub chains
    def add_to_xnat_and_run_freesurfer(self, is_first_scan, set_sub_and_exp_attrs, labels):
        """Construct the celery chain that performs XNAT functions and updates MBAM database with XNAT IDs

        Constructs the chain to upload a file to XNAT and update user, experiment, and scan representations in the MBAM
        database, and if the file is a dicom, appends to that chain a chain that runs dicom conversion, and finally
        sets the error handler on the chain.

        :return: Celery chain that performs XNAT functions
        """

        from cookiecutter_mbam.mbam_logging import app_logger
        #app_logger.error(self.xnat_labels)

        if self.dcm:
            xnat_chain = chain(self._upload_file_to_xnat(is_first_scan, set_sub_and_exp_attrs), self._convert_dicom())
        else:
            xnat_chain = self._upload_file_to_xnat(is_first_scan, set_sub_and_exp_attrs)

        xnat_chain = xnat_chain | self._trigger_job(json.dumps(self._run_freesurfer_on_scan(labels)))

        return xnat_chain.set(
            #link=self._run_freesurfer_on_scan(labels),
            link_error=self._error_handler(log_message='generic_message',
                                           user_message='user_external_uploads',
                                           email_admin=True)
        )
    # todo: upload to cloud storage
    def _run_freesurfer_on_scan(self, labels):
        ds = DerivationService([self.scan])
        ds.create('freesurfer_recon_all')

        return chain(
            self.get_attribute(self.scan.id, attr='xnat_id'),
            self.xc._gen_fs_recon_data(labels),
            self.xc.launch_and_poll_for_completion('freesurfer_recon_all'),
            ds.update_derivation_model('status', exception_on_failure=True)
        )



    def _upload_file_to_xnat(self, is_first_scan, set_attrs):
        """Construct a Celery chain to upload a file to XNAT

        Constructs a chain that uploads the scan file to XNAT, updates the user, experiment, and subject in the MBAM
        database with their XNAT attributes, updates the status of the scan object to affirm that it was successfully
        uploaded, and gets the scan URI to pass to the dicom conversion chain.

        :return: the chain to upload a file to XNAT
        """

        error_proc = [self._error_handler(log_message='generic_message', user_message='user_external_uploads'),
                              self.set_attribute(self.scan.id, 'xnat_status', val='Error')]

        #self.xnat_labels is wrong here

        return chain(
            self.xc.upload_scan_file(self.local_path, self.xnat_labels, import_service=self.dcm,
                                     is_first_scan=is_first_scan, set_attrs=set_attrs),
            self.set_attributes(self.scan.id, passed_val=True),
            self.set_attribute(self.scan.id, 'xnat_status', val='Uploaded'),
            self.get_attribute(self.scan.id, attr='xnat_uri')
            ).set(link_error=error_proc)

    def _convert_dicom(self):
        """Construct a chain to perform conversion of dicoms to nifti

        Constructs a chain that launches the dicom conversion command, polls the container service to check for
        completed dicom conversion, and on completion updates the derivation model with the new derivation status,
        downloads the completed nifti file from XNAT, uploads it to the cloud storage, and updates the derivation model
        with the new cloud storage key.

        :return: the chain to be executed
        """

        return chain(
            self._convert_dicom_to_nifti(),
            self._download_file(),
            self._upload_derivation_to_cloud_storage()
        )

    def _convert_dicom_to_nifti(self):
        """Construct a chain to convert dicom files to NIFTI

        Chains together a chain generated by XNATConnection (which launches the task for dicom to nifti conversion and
        polls the container service to check whether it is complete) and a derivation service task (which updates the
        derivation model with its status). The derivation service task will raise an exception and interrupt the chain
        (and the larger XNAT chain) if dicom conversion was not successful.

        :return: a chain of Celery tasks to convert a DICOM file to NIFTI
        """
        self.ds = DerivationService([self.scan])
        self.ds.create('dicom_to_nifti')

        return chain(
            self.xc.gen_dicom_conversion_data(),
            self.xc.launch_and_poll_for_completion('dicom_to_nifti'),
            self.ds.update_derivation_model('status', exception_on_failure=True),
        )

    def _download_file(self):
        """Construct a chain to download converted nifti file from XNAT

         Chains together the task to fetch the XNAT uri and the task to download a nifti file from XNAT

        :return: a chain of Celery tasks to download a file from XNAT
        """
        return chain(
            self.get_attribute(self.scan.id, attr='xnat_uri', passed_val=False),
            self.xc.dl_file_from_xnat(self.file_depot)
        )

    def _upload_derivation_to_cloud_storage(self):
        """Construct a chain to upload a derivation to cloud storage

        Constructs a chain to upload a scan to cloud storage and update the derivation model. This method differs
        from self._cloud_storage_upload_chain only in including the derivation model updating.

        :return: a chain of Celery tasks to upload a scan to cloud storage
        """
        return chain(
            self.csc.upload_to_cloud_storage(self.file_depot, self.scan_info),
            self.ds.update_derivation_model('cloud_storage_key', exception_on_failure=False)
        )

    def _add_scan_to_database(self, xnat_status='Pending', aws_status='Pending'):
        """Add a scan to the database

        Creates the scan object, adds it to the database, and sets the initial xnat and cloud storage status
        :return: scan
        """
        return Scan.create(experiment_id=self.experiment.id, xnat_status=xnat_status, aws_status=aws_status)

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







