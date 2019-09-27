# -*- coding: utf-8 -*-
"""Experiment service.
"""

from copy import deepcopy
from functools import reduce
from celery import group, chain
from .models import Experiment
from cookiecutter_mbam.base import BaseService
from .tasks import set_experiment_attribute, get_experiment_attribute, set_sub_and_exp_xnat_attrs
from cookiecutter_mbam.scan import ScanService
from cookiecutter_mbam.xnat.service import XNATConnection as XC
from cookiecutter_mbam.config import config_by_name, config_name

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

tasks = {'set_attribute': set_experiment_attribute, 'get_attribute': get_experiment_attribute}

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

    def add(self, user, date, scanner, field_strength, files=None):
        self.experiment = Experiment.create(date=date, scanner=scanner, field_strength=field_strength, user_id=user.id)
        self.xnat_labels, self.attrs_to_set = self.xc.sub_exp_labels(self.user, self.experiment)

        add_scans_to_cloud_storage, add_scans_to_xnat_and_run_freesurfer = self._add_scans(files)

        #todo: add error handling here.  there already is some error handling on xnat job
        add_scans_to_cloud_storage.apply_async()

        add_scans_to_xnat_and_run_freesurfer.apply_async()


    # todo: think about whether it would be simpler to call create resources once for sub and exp
    # and then later for scan, resource.  It avoids one of the reasons for these first_scan calculations
    # otoh: the first_scan conditionals are probably unavoidable for the set_sub_and_exp_attrs question
    # and also the dicom-nifti different also demands some calculation about what you send to create_resources
    # so in context may not be that simplifying
    def _add_scans(self, files):

        scan_services = [self._init_scan_service_and_add_scan_to_database(file) for file in files]


        add_scans_to_cloud_storage = [ss.add_to_cloud_storage() for ss in scan_services]

        add_scans_to_xnat_and_run_freesurfer = [
            ss.add_to_xnat_and_run_freesurfer(*self._gen_xnat_info(i)) for i, ss in enumerate(scan_services)
        ]

        cloud_storage_job = group(add_scans_to_cloud_storage)

        xnat_job = reduce((lambda x, y: chain(x, y)), add_scans_to_xnat_and_run_freesurfer)

        return cloud_storage_job, xnat_job

    def _init_scan_service_and_add_scan_to_database(self, file):
        ss = ScanService(self.user, self.experiment)
        ss.add_to_database(file, deepcopy(self.xnat_labels))
        return ss

    def _gen_xnat_info(self, scan_index):
        first_scan = not scan_index
        set_xnat_attributes = self._set_subject_and_experiment_attributes(first_scan)
        labels = [self.xnat_labels[level]['xnat_label'] for level in ['subject', 'experiment']]
        return [first_scan, set_xnat_attributes, labels]


    def _set_subject_and_experiment_attributes(self, first_scan):

        if not len(self.attrs_to_set) or not first_scan:
            return None
        else:
            return set_sub_and_exp_xnat_attrs.s(self.xnat_labels, self.user.id, self.experiment.id, self.attrs_to_set)



