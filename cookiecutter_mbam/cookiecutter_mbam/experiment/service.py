# -*- coding: utf-8 -*-
"""Experiment service.
"""

from copy import deepcopy
from functools import reduce
from celery import group, chain
from cookiecutter_mbam.base import BaseService
from cookiecutter_mbam.scan import ScanService
from cookiecutter_mbam.xnat.service import XNATConnection as XC
from cookiecutter_mbam.config import config_by_name, config_name
from .models import Experiment
from .tasks import set_experiment_attribute, get_experiment_attribute, set_sub_and_exp_xnat_attrs

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

tasks = {'set_attribute': set_experiment_attribute, 'get_attribute': get_experiment_attribute}

# TODO!!!!!!! the way upload of Freesurfer output to XNAT is set up is dramatically wrong right now.  Subsequent scans
# will overwrite prior ones.  Fix this.

class ExperimentService(BaseService):

    def __init__(self, user, tasks=tasks):
        super().__init__(Experiment)
        self.user = user
        self.scan_services=[]
        self.tasks = tasks
        self._config_read()

    def _config_read(self):
        """
        Obtains the configuration with config_by_name, and sets the upload path and creates XNAT Connection and a Cloud
        Storage Connection instance and attaches them to the scan service object.
        :return: None
        """
        config = config_by_name[config_name]
        self.xc = XC(config=config.XNAT)

    # todo: questions to answer.  1) what happens when you've already called a link_error task on a sub proc
    # todo: idea: rather than email the user on error, email user one summary email with success or failure of upload
    # process
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

        add_scans_to_cloud_storage, add_scans_to_xnat_and_run_freesurfer = self._add_scans(files)

        add_scans_to_cloud_storage.apply_async()

        add_scans_to_xnat_and_run_freesurfer.apply_async(
            link_error=self._error_handler(log_message='generic_message',
                                           user_message='user_cloud_storage',
                                           email_admin=True)
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

        add_scans_to_xnat_and_run_freesurfer = [
            ss.add_to_xnat_and_run_freesurfer(*self._gen_xnat_info(i)) for i, ss in enumerate(scan_services)
        ]

        cloud_storage_job = group(add_scans_to_cloud_storage)

        xnat_job = reduce((lambda x, y: chain(x, y)), add_scans_to_xnat_and_run_freesurfer)

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

        Generates three arguments: a boolean indicating whether the scan is the first to be uploaded for this
        experiment, the signature of the task to set subject and experiment attributes (or None if those attributes
        don't need to be set), and

        :param scan_index: the position of the current scan among scans being currently uploaded
        :type scan_index: int
        :return: a boolean indicating whether the scan is the first scan, the signature of task to set subject and
        experiment XNAT attributes (or None), and a list of subject and experiment XNAT labels
        :rtype: list
        """
        first_scan = not scan_index
        set_xnat_attributes = self._set_subject_and_experiment_attributes(first_scan)
        return [first_scan, set_xnat_attributes]


    def _set_subject_and_experiment_attributes(self, first_scan):
        """

        :param first_scan: whether the scan is the first to be uploaded for this experiment
        :type first_scan: bool
        :return: the signature of the task to set XNAT and experiment attributes (or None)
        :rtype: Union([None, celery.canvas.Signature])
        """

        if not len(self.attrs_to_set) or not first_scan:
            return None
        else:
            return set_sub_and_exp_xnat_attrs.s(self.xnat_labels, self.user.id, self.experiment.id, self.attrs_to_set)



