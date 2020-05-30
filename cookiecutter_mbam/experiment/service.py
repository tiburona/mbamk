# -*- coding: utf-8 -*-
"""Experiment service.
"""

from copy import deepcopy
from functools import reduce
from celery import group, chain
from cookiecutter_mbam.base import BaseService
from cookiecutter_mbam.scan.service import ScanService
from cookiecutter_mbam.xnat.service import XNATConnection as XC
from cookiecutter_mbam.config import Config as config
from .models import Experiment
from .tasks import set_experiment_attribute, get_experiment_attribute, set_sub_and_exp_xnat_attrs, construct_status_email


from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

tasks = {'set_attribute': set_experiment_attribute, 'get_attribute': get_experiment_attribute}

class ExperimentService(BaseService):

    def __init__(self, user, tasks=tasks):
        super().__init__(Experiment)
        self.user = user
        self.scan_services = []
        self.tasks = tasks
        self.xc = XC()

    def add(self, user, date, scanner, field_strength, files=None):
        """ The top level public method for adding an experiment and scans

        Calls methods to add an experiment to the database, generate the XNAT labels for the subject and experiment, and
        kick off the Celery processes to upload scans to cloud storage, upload them to XNAT, and run Freesurfer.

        :param user: a proxy for the current user
        :type user: werkzeug.local.LocalProxy
        :param date: the date of the experiment
        :type date: datetime.date
        :param scanner: the type of scanner
        :type scanner: str
        :param field_strength: the field strength of the scanner
        :param files: files to upload
        :type files: list
        :return: None
        """

        self.experiment = Experiment.create(date=date, scanner=scanner, field_strength=field_strength, user_id=user.id)
        self.xnat_labels, self.attrs_to_set = self.xc.sub_exp_labels(self.user, self.experiment)

        add_scans_to_cloud_storage, add_scans_to_xnat_and_trigger_3d_procs = self._add_scans(files)

        header = group([add_scans_to_cloud_storage, add_scans_to_xnat_and_trigger_3d_procs])

        # `callback` will execute after freesurfer recon is *triggered*, not after the 3d procs complete.
        # By setting `callback'`s `link_error` to itself, the upload status email task executes on error or success.
        callback = self._send_upload_status_email()
        #callback.set(link_error=self._send_upload_status_email())
        job = chain(header, callback)

        job.apply_async(link_error=self._send_upload_status_email())
        #job.apply_async()

    def _send_upload_status_email(self):
        """ Construct a Celery chain to send the user an email with the status of their scan upload

        :return: the Celery chain that sends the user a status email
        :rtype:
        """

        return chain(
            construct_status_email.si(self.experiment.id),
            self._send_email()
        )

    def _add_scans(self, files):
        """Construct the cloud storage and XNAT celery jobs for all scans

        Generates a scan service for every scan and calls scan service methods to generate the signatures of the cloud
        storage upload job (a group) and the XNAT job (a chain)

        :param files: list of scan file objects
        :type files: list
        :return: a two-tuple of the Celery signatures for the cloud storage upload group and
        :rtype: tuple
        """

        scan_services = [self._init_scan_service_and_add_scan_to_database(file) for file in files]

        add_scans_to_cloud_storage = [ss.add_to_cloud_storage() for ss in scan_services]

        add_to_xnat_run_fs_generate_mesh = [
            ss.add_to_xnat_run_fs_generate_mesh(*self._gen_xnat_info(i)) for i, ss in enumerate(scan_services)
        ]

        cloud_storage_job = group(add_scans_to_cloud_storage)

        xnat_job = reduce((lambda x, y: chain(x, y)), add_to_xnat_run_fs_generate_mesh)

        return cloud_storage_job, xnat_job

    def _init_scan_service_and_add_scan_to_database(self, file):
        """Initialize a scan service for a single scan and add that scan to the database

        :param file: the file object
        :type file: werkzeug.datastructures.FileStorage
        :return: the scan service
        :rtype: cookiecutter_mbam.scan.service.ScanService
        """

        ss = ScanService(self.user, self.experiment)
        ss.add_to_database(file, deepcopy(self.xnat_labels))

        return ss

    def _gen_xnat_info(self, scan_index):
        """Generate the arguments for the scan service method that adds a scan to XNAT and runs Freesurfer

        Generates two arguments: a boolean indicating whether the scan is the first to be uploaded for this
        experiment, the signature of the task to set subject and experiment attributes (or None if those attributes
        don't need to be set)

        :param scan_index: the position of the current scan among scans being currently uploaded
        :type scan_index: int
        :return: a boolean indicating whether the scan is the first scan, the signature of task to set subject and
        experiment XNAT attributes (or None), and a list of subject and experiment XNAT labels
        :rtype: list
        """
        first_scan = not scan_index
        set_xnat_attributes = self._set_subject_and_experiment_attributes(first_scan)
        return [first_scan, set_xnat_attributes]

    # XNAT attributes will only be set on subject and experiment attributes at the moment the scan is uploaded, and they
    # only need to be set if they haven't been already.
    def _set_subject_and_experiment_attributes(self, first_scan):
        """Generate a signature for the task to set subject and experiment attributes (or None if they won't be set)

        :param first_scan: whether the scan is the first to be uploaded for this experiment
        :type first_scan: bool
        :return: the signature of the task to set XNAT and experiment attributes (or None)
        :rtype: Union([None, celery.canvas.Signature])
        """

        if not len(self.attrs_to_set) or not first_scan:
            return None
        else:
            return set_sub_and_exp_xnat_attrs.s(self.xnat_labels, self.user.id, self.experiment.id, self.attrs_to_set)
