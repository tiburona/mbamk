# -*- coding: utf-8 -*-
"""Scan service.

This module implements uploading a scan file to XNAT and adding a scan to the database.

Todo: do we want to infer file type from extension?  Or use some other method?

Todo: Right now if we use the import service XNAT is inferring its own scan id.  What do we want to do about that?

Todo: if someone uploads a zip file we don't actually know that there are dicoms inside (could be NIFTI).  Consider this
fact.

Todo: Need to think more about recording status of uploads in database since scan object is going to be created regardless.  Should scan have field like container
path?

"""

import configparser
from celery import group, chain
from cookiecutter_mbam.user import User
from cookiecutter_mbam.experiment import Experiment
from .models import Scan
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.storage import CloudStorageConnection
from cookiecutter_mbam.derivation import DerivationService
from cookiecutter_mbam.experiment import ExperimentService
from cookiecutter_mbam.user import UserService
from .utils import gzip_file
from cookiecutter_mbam.xnat.tasks import *
from .tasks import set_scan_attribute, get_scan_attribute, set_scan_attributes
from cookiecutter_mbam.base_service.models import BaseService

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

tasks = {'set_attribute': set_scan_attribute, 'get_attribute': get_scan_attribute,
         'set_attributes': set_scan_attributes}

class ScanService(BaseService):
    def __init__(self, user_id, exp_id, config_dir='', tasks=tasks):
        super().__init__(Scan)
        self.user_id = user_id
        self.user = User.get_by_id(self.user_id)
        self.experiment = Experiment.get_by_id(exp_id)
        self.instance_path = current_app.instance_path[:-8]
        if not len(config_dir):
            config_dir = self.instance_path
        self._config_read(os.path.join(config_dir, 'setup.cfg'))
        self.tasks = tasks

    def _config_read(self, config_path):
        """Scan service configuration
        Reads the config file passed on scan service object creation, and sets the upload path and creates XNAT
        Connection and a Cloud Storage Connection instance and attaches them to the scan service object.
        :param str config_path:
        :return: None
        """
        config = configparser.ConfigParser()
        config.read(config_path)
        self.file_depot = os.path.join(self.instance_path, config['files']['file_depot'])
        self.xc = XNATConnection(config=config['XNAT'])
        self.csc = CloudStorageConnection(config=config['AWS'])

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
        """
        _, ext = os.path.splitext(filename)
        filename = os.path.basename(filename)
        local_path = os.path.join(self.file_depot, filename)
        return ext, filename, local_path

    def _compress_file(self, local_path, filename):
        image_file, gz_path = gzip_file(local_path)
        os.remove(local_path)
        local_path = gz_path
        filename = filename + '.gz'
        return image_file, local_path, filename

    def _await_external_uploads(self):
        """The method to start the Celery chain that uploads scans to XNAT and cloud storage

        Calls the methods to construct the chain that uploads the file to cloud storage and to construct
        the chain that uploads the file to XNAT, and runs both these chains in parallel.

        :return: None
        """
        job = group([self._cloud_storage_upload_chain(), self._xnat_chain()])
        job.apply_async()

    def _cloud_storage_upload_chain(self):
        return self.csc.upload_chain(self.filename, self.file_depot, self.scan_info)

    def _xnat_chain(self):
        """Construct the celery chain that performs XNAT functions and updates MBAM database with XNAT IDs

        Constructs the chain to upload a file to XNAT and update user, experiment, and scan representations in the MBAM
        database, and if the file is a dicom, append to that chain a chain that conducts dicom conversion, and finally
        set the error handler on the chain.

        :return: Celery chain that performs XNAT functions
        """

        if self.dcm:
            xnat_chain = self.upload_file_to_xnat() | self._convert_dicom()
        else:
            xnat_chain = self.upload_file_to_xnat()

        return xnat_chain.set(link_error=self._error_handler(log_message='generic_message',
                                                             user_message='user_external_uploads'))

    def upload_file_to_xnat(self):

        error_proc = [self._error_handler(log_message='generic_message', user_message='user_external_uploads'),
                              self.set_attribute(self.scan.id, 'xnat_status', val='error')]

        return chain(
            self.xc.upload_scan_file(file_path=self.local_path, import_service=self.dcm),
            self._update_database_objects(),
            self.set_attribute(self.scan.id, 'xnat_status', val='uploaded'),
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
            self._upload_file_to_cloud_storage()
        )

    def _update_database_objects(self):
        """Create the signature of update_database_objects task

        Construct the signature of the update_database_objects task, passing it model names, model ids, keywords, and
        xnat_ids arguments. This is basically the same functionality as set_attribute.  However, in this particular
        case, if a scan is imported, the scan uri is not known until the file is imported and the chain is executed.
        For this reason, a specialized method is needed.

        :return: the signature of the Celery task to update database objects
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
        self.ds = DerivationService(self.scan.id)
        self.ds.create('dicom_to_nifti')

        return chain(
            self.xc.launch_and_poll_for_completion('dicom_to_nifti'),
            self.ds.update_derivation_model('status', exception_on_failure=True),
        )

    def _download_file(self):
        return chain(
            self.get_attribute(self.scan.id, attr='xnat_uri', passed_val=False),
            self.xc.dl_file_from_xnat(self.file_depot),
        )

    def _upload_file_to_cloud_storage(self):
        return chain(
            self.csc.ul_scan_to_cloud_storage(self.filename, self.file_depot, self.scan_info),
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

        Deletes a scan from the database and optionally deletes it from XNAT. Only admins should delete a scan from XNAT

        :param int scan_id: the database id of the scan to delete
        :param bool delete_from_xnat: whether to delete the scan file from XNAT, default False
        :return: None
        """
        scan = Scan.get_by_id(scan_id)
        if delete_from_xnat:
            self.xc.xnat_delete(scan.xnat_uri)
            self.experiment.update(num_scans=self.experiment.num_scans - 1)
        scan.delete()







