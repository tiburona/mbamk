# -*- coding: utf-8 -*-
"""Scan service.

This module implements uploading a scan file to XNAT and adding a scan to the database.

Todo: do we want to infer file type from extension?  Or use some other method?

Todo: Right now if we use the import service XNAT is inferring its own scan id.  What do we want to do about that?

Todo: if someone uploads a zip file we don't actually know that there are dicoms inside (could be NIFTI).  Consider this
fact.

Todo: figure out why redis-server not running doesn't get caught as Exception.  Figure out how to catch it.

"""

from celery import group, chain
from cookiecutter_mbam.config import config_by_name, config_name
from cookiecutter_mbam.user import User
from cookiecutter_mbam.experiment import Experiment
from .models import Scan
from cookiecutter_mbam.base.models import BaseService
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.storage import CloudStorageConnection
from cookiecutter_mbam.derivation import DerivationService
from cookiecutter_mbam.experiment import ExperimentService
from cookiecutter_mbam.user import UserService
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
    def __init__(self, user_id, exp_id, tasks=tasks):
        super().__init__(Scan)
        self.user_id = user_id
        self.user = User.get_by_id(self.user_id)
        self.experiment = Experiment.get_by_id(exp_id)
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

    def add(self, image_file):
        """The top level public method for adding a scan

        Calls methods to infer file type and further process the file, generate xnat identifiers and query strings,
        check what XNAT identifiers objects have, add the scan to the database, and finally begin the process of
        uploading the file to external sites.

        :param file_object image_file: the file object
        :return: None

        """
        self.local_path, self.filename, self.dcm = self._process_file(image_file)

        self.scan_info = self.xc.generate_xnat_identifiers(self.user, self.experiment, dcm=self.dcm)

        self.scan = self._add_scan_to_database()

        try:
            self._await_external_uploads()
        except Exception as e:
             self._call_error_handler(e, log_message='generic_message', user_message='user_external_uploads')

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

    def _await_external_uploads(self):
        """Start the Celery chain that uploads scans to XNAT and cloud storage

        Calls the methods to construct the chain that uploads the file to cloud storage and the chain that uploads the
        file to XNAT, and runs both these chains in parallel.

        :return: None
        """
        job = group([self._cloud_storage_chain(), self._xnat_chain()])
        job.apply_async()

    def _cloud_storage_chain(self):
        """Construct the celery chain to upload an original scan file to cloud storage

        :return: Celery chain that uploads a scan to cloud storage
        """
        return chain(
            self.csc.upload_to_cloud_storage(self.filename, self.file_depot, self.scan_info),
            self.set_attribute(self.scan.id, 'orig_aws_key', passed_val=True)
        )

    def _xnat_chain(self):
        """Construct the celery chain that performs XNAT functions and updates MBAM database with XNAT IDs

        Constructs the chain to upload a file to XNAT and update user, experiment, and scan representations in the MBAM
        database, and if the file is a dicom, appends to that chain a chain that runs dicom conversion, and finally
        sets the error handler on the chain.

        :return: Celery chain that performs XNAT functions
        """

        if self.dcm:
            xnat_chain = self._upload_file_to_xnat() | self._convert_dicom()
        else:
            xnat_chain = self._upload_file_to_xnat()

        return xnat_chain.set(link_error=self._error_handler(log_message='generic_message',
                                                             user_message='user_external_uploads',
                                                             email_admin=True))

    def _upload_file_to_xnat(self):
        """Construct a Celery chain to upload a file to XNAT

        Constructs a chain that uploads the scan file to XNAT, updates the user, experiment, and subject in the MBAM
        database with their XNAT attributes, updates the status of the scan object to affirm that it was successfully
        uploaded, and gets the scan URI to pass to the dicom conversion chain.

        :return: the chain to upload a file to XNAT
        """

        error_proc = [self._error_handler(log_message='generic_message', user_message='user_external_uploads'),
                              self.set_attribute(self.scan.id, 'xnat_status', val='Error')]

        return chain(
            self.xc.upload_scan_file(file_path=self.local_path, import_service=self.dcm),
            self._update_database_objects(),
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

    def _update_database_objects(self):
        """Create the signature of update_database_objects task

        Constructs a chain of signature of tasks to update user, experiment, and scan with their IDs and URIs in XNAT.
        Because in the case of scan the ID and URI are not known a priori (at least if the scan is an imported dicom),
        scan must accept its new attributes as arguments passed from the signature of the task executed just before,
        part of xc.upload_scan_file.

        :return: a chain of Celery tasks to update database objects
        """

        es = ExperimentService()
        us = UserService()

        exp_attrs = {'xnat_id': self.scan_info[1], 'xnat_uri': self.xc.xnat_experiment_uri(self.scan_info[1])}
        subj_attrs = {'xnat_id': self.scan_info[0], 'xnat_uri': self.xc.xnat_subject_uri(self.scan_info[0])}

        return chain(
            self.set_attributes(self.scan.id, passed_val=True),
            es.set_attributes(self.experiment.id, exp_attrs),
            us.set_attributes(self.user_id, subj_attrs)
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
            self.xc.dl_file_from_xnat(self.file_depot),
        )

    def _upload_derivation_to_cloud_storage(self):
        """Construct a chain to upload a derivation to cloud storage

        Constructs a chain to upload a scan to cloud storage and update the derivation model. This method differs
        from self._cloud_storage_upload_chain only in including the derivation model updating.

        :return: a chain of Celery tasks to upload a scan to cloud storage
        """
        return chain(
            self.csc.upload_to_cloud_storage(self.filename, self.file_depot, self.scan_info),
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







