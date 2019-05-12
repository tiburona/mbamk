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
from celery import group, chord
from cookiecutter_mbam.user import User
from cookiecutter_mbam.experiment import Experiment
from .models import Scan
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.storage import CloudStorageConnection
from cookiecutter_mbam.derivation import Derivation
from .utils import gzip_file
from cookiecutter_mbam.xnat.tasks import *
from cookiecutter_mbam.storage.tasks import upload_scan_to_cloud_storage
from cookiecutter_mbam.derivation.tasks import update_derivation_model
from .tasks import update_database_objects, get_attributes
from cookiecutter_mbam.settings import MAIL_PASSWORD
from cookiecutter_mbam.utility.celery_utils import send_email, error_handler



from flask import current_app


def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


class ScanService:
    def __init__(self, user_id, exp_id, config_dir=''):
        self.user_id = user_id
        self.user = User.get_by_id(self.user_id)
        self.experiment = Experiment.get_by_id(exp_id)
        self.instance_path = current_app.instance_path[:-8]
        if not len(config_dir):
            config_dir = self.instance_path
        self._config_read(os.path.join(config_dir, 'setup.cfg'))

    def _config_read(self, config_path):
        """Scan service configuration
        Reads the config file passed on scan service object creation, and sets the upload path and creates XNAT
        Connection and a Cloud Storage Connection instance and attaches them to the scan service object.
        :param config_path:
        :return: None
        """
        config = configparser.ConfigParser()
        config.read(config_path)
        self.file_depo = os.path.join(self.instance_path, config['files']['file_depo'])
        self.xc = XNATConnection(config=config['XNAT'])
        self.csc = CloudStorageConnection(config=config['AWS'])

    def add(self, image_file):
        """The top level public method for adding a scan

        Calls methods to infer file type and further process the file, generate xnat identifiers and query strings,
        check what XNAT identifiers objects have, add the scan to the database, and finally begin the process of
        uploading the file to external sites.

        :param file object image_file: the file object
        :return: None

        """
        self.local_path, self.filename, self.dcm = self._process_file(image_file)

        self.xnat_ids = self._generate_xnat_identifiers(dcm=self.dcm)
        self.existing_xnat_ids = self._check_for_existing_xnat_ids()
        self.scan_info = (self.xnat_ids['subject']['xnat_id'], self.xnat_ids['experiment']['xnat_id'],
                          self.xnat_ids['scan']['xnat_id'])

        # todo: update scan's status on successful upload to XNAT
        self.scan = self._add_scan_to_database()  # todo: what should scan's string repr be?


        self._await_external_uploads()

    def _process_file(self, image_file):
        """Prepare file for upload to XNAT and cloud storage

        :param image_file:
        :return: two-tuple of the path to the file on local disk and a boolean indicating if the file is a zip file
        """
        name, ext = os.path.splitext(image_file.filename)
        filename = os.path.basename(image_file.filename)
        local_path = os.path.join(self.file_depo, filename)
        image_file.save(local_path)
        if ext == '.nii':
            image_file, gz_path = gzip_file(local_path)
            os.remove(local_path)
            local_path = gz_path
            filename = filename + '.gz'
        image_file.close()
        dcm = ext == '.zip'
        return (local_path, filename, dcm)

    def _generate_xnat_identifiers(self, dcm=False):
        """Generate object ids for use in XNAT

        Creates a dictionary with keys for type of XNAT object, including subject, experiment, scan, resource and file.
        The values in the dictionary are dictionaries with keys 'xnat_id' and, optionally, 'query_string'.  'xnat_id'
        points to the identifier of the object in XNAT, and 'query_string' to the query that will be used in the put
        request to create the object.

        :return: xnat_id dictionary
        :rtype: dict
        """
        xnat_ids = {}

        xnat_ids['subject'] = {'xnat_id': str(self.user_id).zfill(6)}

        xnat_exp_id = '{}_MR{}'.format(xnat_ids['subject']['xnat_id'], self.user.num_experiments)
        exp_date = self.experiment.date.strftime('%m/%d/%Y')
        xnat_ids['experiment'] = {'xnat_id': xnat_exp_id,
                                  'query_string': '?xnat:mrSessionData/date={}'.format(exp_date)}

        scan_number = self.experiment.num_scans + 1
        xnat_scan_id = 'T1_{}'.format(scan_number)
        xnat_ids['scan'] = {'xnat_id': xnat_scan_id, 'query_string': '?xsiType=xnat:mrScanData'}

        if dcm:
            resource = 'DICOM'
        else:
            resource = 'NIFTI'
        xnat_ids['resource'] = {'xnat_id': resource}

        xnat_ids['file'] = {'xnat_id': 'T1.nii.gz', 'query_string': '?xsi:type=xnat:mrScanData'}

        return xnat_ids

    def _check_for_existing_xnat_ids(self):
        """Check for existing attributes on the user and experiment

        Generates a dictionary with current xnat_subject_id for the user, xnat_experiment_id for the experiment as
        values if they exist (empty string if they do not exist).

        :return: a dictionary with two keys with the xnat subject id and xnat experiment id.
        :rtype: dict
        """
        return {k: getattr(v, k) if getattr(v, k) else '' for k, v in {'xnat_subject_id': self.user,
                                                                       'xnat_experiment_id': self.experiment}.items()}

    def _await_external_uploads(self):
        """The method to start the Celery chain that uploads scans to XNAT and cloud storage

        Calls the method to construct the chain that uploads the file to cloud storage, calls the method to construct
        the chain that uploads the file to XNAT, and finally, runs the cloud storage upload chain and XNAT upload chain
        in parallel.

        :return: None
        """

        #raise Exception

        cloud_storage_upload_chain = self.csc.upload_chain(self.filename, self.file_depo, self.scan_info).set(
            link_error=[])

        xnat_chain = self._construct_xnat_chain()

        job = group([cloud_storage_upload_chain, xnat_chain])
        job.apply_async()

    def _construct_xnat_chain(self):
        """Construct the celery chain that performs XNAT functions and updates MBAM databse

        Constructs the chain to upload a file to XNAT and update user, experiment, and scan representations in the MBAM
        database, and if the file is a dicom, append to that chain a chain that conducts dicom conversion, and finally
        set the error handler on the chain.

        :return: Celery chain that performs XNAT functions
        """

        email_info = (MAIL_PASSWORD, self.user.email, "Something went wrong with XNAT.")

        xnat_upload_chain = \
            self.xc.upload_chain(
                ids=(self.xnat_ids, self.existing_xnat_ids),
                file_path=self.local_path,
                import_service=self.dcm
            ) | \
            self._update_database_objects_sig()

        if self.dcm:
            dicom_conversion_chain = self._dicom_conversion_chain(self.scan)
            xnat_chain = xnat_upload_chain | dicom_conversion_chain
        else:
            xnat_chain = xnat_upload_chain

        return xnat_chain.set(link_error=error_handler.s(email_info))


    def _update_database_objects_sig(self):
        """Create the signature of update_database_objects task

        Construct the signature of the update_database_ojbects task, passing it model names, model ids, keywords, and
        xnat_ids arguments.

        :return: the signature of the Celery task to update database objects
        """
        return update_database_objects.s(
            model_names = ['user', 'experiment', 'scan'],
            model_ids = [self.user_id, self.experiment.id, self.scan.id],
            keywords = ['subject', 'experiment', 'scan'],
            xnat_ids = self.scan_info
        )

    def _dicom_conversion_chain(self):
        """Construct a chain to perform conversion of dicoms to nifti

        Constructs a chain that launches the dicom conversion command, pools the container service to check for
        completed dicom converstion, and on completion updates the derivation model with the new derivation status,
        downloads the completed nifti file from XNAT, uploads it to the cloud storage, and updates the derivation model
        with the new cloud storage key.

        :return: the chain to be executed
        """

        xnat_credentials = (self.xc.server, self.xc.user, self.xc.password)
        process_name = 'dicom_to_nifti'
        if self.xc.xnat_config['local_docker'] == 'False':
            process_name += '_transfer'
        nifti = Derivation.create(scan_id=self.scan.id, process_name=process_name, status='pending')
        command_ids = self.xc._generate_ids('dicom_to_nifti')

        chain = launch_command.s(xnat_credentials, self.xc.project, command_ids) | \
                poll_cs.s(xnat_credentials) | \
                update_derivation_model.s(nifti.id, 'status') | \
                get_attributes.s(('scan', self.scan.id, 'xnat_uri'), ('derivation', nifti.id, 'status')) | \
                dl_file_from_xnat.s(xnat_credentials, self.file_depo) | \
                upload_scan_to_cloud_storage.s(self.file_depo, self.csc.bucket_name, self.csc.auth, self.scan_info) | \
                update_derivation_model.s(nifti.id, 'cloud_storage_key')

        return chain

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




