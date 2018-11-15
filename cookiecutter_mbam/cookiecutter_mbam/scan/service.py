# -*- coding: utf-8 -*-
"""Scan service.

This module implements uploading a scan file to XNAT and adding a scan to the database.

Todo: Maybe the public method should be called add, and that should kick off an upload procedure, rather than the
other way around.

Todo: do we want to infer file type from extension?  Or use some other method?

Todo: Right now if we use the import service XNAT is inferring its own scan id.  What do we want to do about that?

Todo: if someone uploads a zip file we don't actually know that there are dicoms inside (could be NIFTI).  Consider this
fact.

Todo: Upload security for zip files?


"""
import os
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.experiment import Experiment
from cookiecutter_mbam.user import User
from .models import Scan
from .utils import gzip_file

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


class ScanService:

    def __init__(self, user_id, exp_id):
        self.user_id = user_id
        self.user = User.get_by_id(self.user_id)
        self.experiment = Experiment.get_by_id(exp_id)
        self.xc = XNATConnection()

    # todo: what is the actual URI of the experiment I've created?  Why does it have the XNAT prefix?
    # maybe that's the accessor?  Is the accessor in the URI?
    def upload(self, image_file):
        """The top level public method for adding a scan

        Calls methods to infer file type and further process the file, generate xnat identifiers and query strings,
        check what XNAT identifiers objects have, upload the scan to XNAT, add the scan to the database, and update
        user, experiment, and scan database objects with their XNAT-related attributes.

        :param file object image_file: the file object
        :return: None

        """
        file, dcm = self._process_file(image_file)
        xnat_ids = self._generate_xnat_identifiers(dcm=dcm)
        existing_attributes = self._check_for_existing_xnat_ids()
        uris = self.xc.upload_scan(xnat_ids, existing_attributes, image_file, import_service=dcm)
        scan = self._add_scan()
        keywords = ['subject', 'experiment', 'scan']
        self._update_database_objects(keywords=keywords, objects=[self.user, self.experiment, scan],
                                     ids=['{}_id'.format(xnat_ids[kw]['xnat_id']) for kw in keywords], uris=uris)

    def _add_scan(self):
        """Add a scan to the database

        Creates the scan object, adds it to the database, and increments the parent experiment's scan count
        :return: scan
        """
        scan = Scan.create(experiment_id=self.experiment.id)
        self.experiment.num_scans += 1
        return scan


    def _process_file(self, image_file):
        """Infer file type from extension and respond to file type as necessary

        Uses file extension to infer whether file should be left alone or gzipped, or whether zip file will be sent to
        import service.

        :param file object image_file: the file object
        :return: a two-tuple of the image file, and a boolean indicating the file type is dcm
        :rtype: tuple

        """
        image_file_name = image_file.filename
        file_name, file_ext = os.path.splitext(image_file_name)
        dcm = False
        if file_ext == '.nii':
            image_file = (gzip_file(image_file, file_name))
        if file_ext == '.zip':
            dcm = True
        return (image_file, dcm)

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
        xnat_ids['experiment'] = {'xnat_id': xnat_exp_id, 'query_string':'?xnat:mrSessionData/date={}'.format(exp_date)}

        scan_number = self.experiment.num_scans + 1
        xnat_scan_id = 'T1_{}'.format(scan_number)
        xnat_ids['scan'] = {'xnat_id':xnat_scan_id, 'query_string':'?xsiType=xnat:mrScanData'}

        if dcm:
            resource = 'DICOM'
        else:
            resource = 'NIFTI'
        xnat_ids['resource'] = {'xnat_id': resource}

        xnat_ids['file'] = {'xnat_id':'T1.nii.gz', 'query_string':'?xsi:type=xnat:mrScanData'}

        return xnat_ids

    def _check_for_existing_xnat_ids(self):
        """Check for existing attributes on the user and experiment

        Generates a dictionary with current xnat_subject_id for the user, xnat_experiment_id for the experiment as
        values if they exist (empty string if they do not exist). A private method not designed to be accessed by other
        classes.

        :return: a dictionary with two keys with the xnat subject id and xnat experiment id.
        :rtype: dict
        """
        return {k: getattr(v, k) if getattr(v, k) else '' for k, v in {'xnat_subject_id': self.user,
                                                                       'xnat_experiment_id': self.experiment}.items()}


    # todo: the check for existence before reassigning the values is verbose.  Decide whether its important.
    def _update_database_objects(self, objects=[], keywords=[], uris=[], ids=[],):
        """Update database objects

        After uploading a scan, ensures that user, experient, and scan are updated in the database with their xnat uri
        and xnat id.

        :param list objects: user, experiment, and scan
        :param list keywords: 'subject', 'experiment', and 'scan'
        :param list uris: xnat uris
        :param list ids: xnat ids
        :return: None
        """
        attributes = zip(objects, keywords, uris, ids)
        for (obj, kw, uri, id) in attributes:
            if not hasattr(obj, 'xnat_uri'):
                obj.update({'xnat_uri': uri})
            if not hasattr(obj,'xnat_{}_id'.format(kw)):
                obj.update({'xnat_{}_id'.format(kw): id})












