# -*- coding: utf-8 -*-
"""Experiment service.
"""
import os
from celery import group, chain
from cookiecutter_mbam import celery
from .models import Experiment
from cookiecutter_mbam.base import BaseService
from .tasks import set_experiment_attribute, get_experiment_attribute
from cookiecutter_mbam.scan import ScanService
from cookiecutter_mbam.derivation import DerivationService
from cookiecutter_mbam.user import UserService
from cookiecutter_mbam.xnat.service import XNATConnection as XC
from cookiecutter_mbam.config import config_by_name, config_name
from cookiecutter_mbam.mbam_logging import app_logger

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

tasks = {'set_attribute': set_experiment_attribute, 'get_attribute': get_experiment_attribute}


class ExperimentService(BaseService):

    def __init__(self, user, tasks=tasks):
        super().__init__(Experiment)
        self.user = user
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
        self.xnat_ids = self.xc.sub_exp_ids(self.user, self.experiment)
        app_logger.error("celery backend in experiment service {}".format(celery.backend), extra={'email_admin': True})
        job = group([self._add_scan(file) for file in files]) | self._update_database_objects() | self._run_freesurfer()
        job.apply_async()

    def _add_scan(self, file):
        ss = ScanService(self.user, self.experiment)
        ss.add(file, self.xnat_ids)
        return ss.upload_and_convert_scan()

    def _run_freesurfer(self):
        self.ds = DerivationService(self.experiment.scans)
        self.ds.create('freesurfer_recon_all')
        data = {
            'scans': ' '.join([scan.xnat_id for scan in self.experiment.scans]),
            'experiment_id': self.experiment.xnat_id
        }

        return chain(
            self.xc.launch_and_poll_for_completion('freesurfer_recon_all', data),
            self.ds.update_derivation_model('status', exception_on_failure=True),
        )

    def _update_database_objects(self):

        us = UserService()

        subj_attrs, exp_attrs = [self.xnat_ids[level] for level in ['subject', 'experiment']]

        return chain(
            us.set_attributes(self.user.id, subj_attrs),
            self.set_attributes(self.experiment.id, exp_attrs)
        )

