# -*- coding: utf-8 -*-
"""Scan service.

This module implements uploading a scan file to XNAT and adding a scan to the database.

Todo: do we want to infer file type from extension?  Or use some other method?

Todo: Right now if we use the import service XNAT is inferring its own scan id.  What do we want to do about that?

Todo: if someone uploads a zip file we don't actually know that there are dicoms inside (could be NIFTI).  Consider this
fact.

Todo: Upload security for zip files?

Todo: I need to make sure that if I catch an exception in XNAT connection I don't go ahead and create a scan in the database.

"""

import os
import configparser
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.xnat.tasks import *
from cookiecutter_mbam.storage import CloudStorageConnection
from cookiecutter_mbam.experiment import Experiment
from cookiecutter_mbam.user import User
from .models import Scan
from cookiecutter_mbam.derivation import Derivation, DerivationService, update_derivation_model
from .utils import gzip_file, crop
from cookiecutter_mbam.storage.tasks import upload_scan

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
        """Scan service configuratino
        Reads the config file passed on scan service object creation, and sets the upload path and creates XNAT
        Connection and a Cloud Storage Connection instance and attaches them to the scan service object.
        :param config_path:
        :return: None
        """
        config = configparser.ConfigParser()
        config.read(config_path)
        # todo: consider changing name of upload_dest if we also use it for downloads
        self.upload_dest = os.path.join(self.instance_path, config['uploads']['uploaded_scans_dest'])
        self.xc = XNATConnection(config=config['XNAT'])
        self.csc = CloudStorageConnection(config=config['AWS'])

    def add(self, image_file):
        """The top level public method for adding a scan

        Calls methods to infer file type and further process the file, generate xnat identifiers and query strings,
        check what XNAT identifiers objects have, upload the scan to cloud storage, upload the scan to XNAT, add the
        scan to the database, update user, experiment, and scan database objects with their XNAT-related attributes,
        and finally, if the uploaded file was zipped file of dicoms, starts the process of conversion to nifti.

        :param file object image_file: the file object
        :return: None

        """
        local_path, filename, dcm = self._process_file(image_file)

        self.xnat_ids = self._generate_xnat_identifiers(dcm=dcm)
        self.existing_xnat_ids = self._check_for_existing_xnat_ids()

        # upload scan to cloud storage
        key = upload_scan(
            filename=filename,
            bucket_name=self.csc.bucket_name,
            dir = self.upload_dest,
            auth = self.csc.auth,
            scan_info = (self.user_id, self.experiment.id, self.xnat_ids['scan']['xnat_id'])
        )

        # upload scan to XNAT
        uris = self.xc.upload_scan(self.xnat_ids, self.existing_xnat_ids, local_path, import_service=dcm)

        scan = self._add_scan_to_database(orig_aws_key=key, dcm=dcm)  # todo: what should scan's string repr be?

        keywords = ['subject', 'experiment', 'scan']
        self._update_database_objects(
            keywords=keywords,
            objects=[self.user, self.experiment, scan],
            ids=[self.xnat_ids[kw]['xnat_id'] for kw in keywords],
            uris=uris
        )

        if dcm: self._dicom_conversion(scan)

    def _dicom_conversion(self, scan):
        """Kick off conversion of dicom file to nifti

        Starts remote dicom conversion via the container service and calls the method that checks for completion

        :param Scan scan: the scan object
        :return: None
        """
        container_id, nifti, derivation_service = self._dicom_to_nifti(scan.id)
        self.dicom2nifti_container_id = container_id
        self.await_dicom_conversion(container_id=container_id, scan=scan, derivation=nifti)

    def await_dicom_conversion(self, container_id, scan, derivation):
        """ Check for and respond to completed dicom conversion

        Polls the container service to check for completed dicom converstion, and on completion updates the derivation
        model with the new derivation status, downloads the completed nifti file from XNAT, uploads it to the cloud
        storage, and updates the derivation model with the new cloud storage key.

        :param str container_id: the id of the launched container
        :param Scan scan: the scan object
        :param Derivation derivation: the derivation object
        :return: None
        """

        xnat_credentials = (self.xc.server, self.xc.user, self.xc.password)
        scan_info = (self.user_id, scan.experiment_id, scan.id)
        chain = poll_cs.s(xnat_credentials, container_id) | \
                update_derivation_model.s(derivation.id, 'status') | \
                dl_file_from_xnat.s(xnat_credentials, self.xc.nifti_files_url(scan), self.upload_dest) | \
                upload_scan.s(self.csc.bucket_name, self.upload_dest, self.csc.auth, scan_info) | \
                update_derivation_model.s(derivation.id, 'cloud_storage_key')
        chain()

    def delete(self, scan_id, delete_from_xnat=False):
        """ Delete a scan from the database

        Deletes a scan from the database and optionally deletes it from XNAT. Only admins should delete a scan from XNAT

        :param int scan_id: the database id of the scan to delete
        :param bool delete_from_xnat: whether to delete the scan file from XNAT, default False
        :return: None
        """
        scan = Scan.get_by_id(scan_id)
        if delete_from_xnat:
            self._delete_from_xnat(self, scan)
            self.experiment.update(num_scans=self.experiment.num_scans - 1)
        scan.delete()

    def _delete_from_xnat(self, scan):
        # todo: consider whether this really needs to be its own method or should just folded into delete
        """
        :param object scan: the database object corresponding to the scan to delete in xnat
        :return: None
        """
        self.xc.xnat_delete(scan.xnat_uri)

    def _add_scan_to_database(self, orig_aws_key, dcm):
        """Add a scan to the database

        Creates the scan object, adds it to the database, and increments the parent experiment's scan count
        :return: scan
        """
        scan = Scan.create(experiment_id=self.experiment.id)
        if dcm:
            scan = scan.update(orig_aws_key=orig_aws_key)
        else:
            scan = scan.update(orig_aws_key=orig_aws_key, nifti_aws_key=orig_aws_key)
        return scan

    def _process_file(self, image_file):
        """Prepare file for upload to XNAT and cloud storage
        :param image_file:
        :return: two-tuple of the path to the file on local disk and a boolean indicating if the file is a zip file
        """
        name, ext = os.path.splitext(image_file.filename)
        filename = os.path.basename(image_file.filename)
        local_path = os.path.join(self.upload_dest, filename)
        image_file.save(local_path)
        if ext == '.nii':
            image_file, gz_path = gzip_file(local_path)
            os.remove(local_path)
            local_path = gz_path
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

    def _update_database_objects(self, objects=[], keywords=[], uris=[], ids=[], ):
        """Update database objects

        After uploading a scan, ensures that user, experiment, and scan are updated in the database with their xnat uri
        and xnat id.

        :param list objects: user, experiment, and scan
        :param list keywords: 'subject', 'experiment', and 'scan'
        :param list uris: xnat uris
        :param list ids: xnat ids
        :return: None
        """
        attributes = zip(objects, keywords, uris, ids)
        for (obj, kw, uri, id) in attributes:
            obj.update(xnat_uri=uri)
            obj.update(**{'xnat_{}_id'.format(kw): id})

    def _dicom_to_nifti(self, scan_id):
        """Convert dicom files to nifti

        When dicom files are uploaded to the container service, creates a new derivation object and use the derivation
        service to launch dicom to nifti conversion.

        :param int scan_id: the id of the scan whose dicom files will be converted
        :return: the id of the container running the process
        :rtype string
        """
        scan = Scan.get_by_id(scan_id)
        nifti = Derivation.create(scan_id=scan.id, process_name='dicom_to_nifti', status='unstarted')
        ds = DerivationService(nifti.id, scan.id)
        scan_data_locator = crop(scan.xnat_uri, '/experiments')
        rv = ds.launch(data={'scan': scan_data_locator})
        container_id = json.loads(rv.text)['container-id']
        nifti.update(status='started')
        return (container_id, nifti, ds)



