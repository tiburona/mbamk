# -*- coding: utf-8 -*-
"""Experiment service.
"""

from functools import reduce
from celery import group, chain, chord
from .models import Experiment
from cookiecutter_mbam.base import BaseService
from .tasks import set_experiment_attribute, get_experiment_attribute, gen_freesurfer_data, set_sub_and_exp_xnat_attrs
from cookiecutter_mbam.scan.tasks import get_scan_attribute
from cookiecutter_mbam.scan import ScanService
from cookiecutter_mbam.derivation import DerivationService
from cookiecutter_mbam.user import UserService
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
        self.xnat_labels, self.existing_labels = self.xc.sub_exp_labels(self.user, self.experiment)
        self.exists_in_xnat = len(self.existing_labels['experiment']['xnat_label'])

        add_scans_to_xnat, add_scans_to_cloud_storage = self._add_scans(files)

        cloud_storage_job = group(add_scans_to_cloud_storage)
        cloud_storage_job.apply_async()

        xnat_job = reduce((lambda x, y: chain(x, y)), add_scans_to_xnat)

        run_freesurfer = chord(self._get_scans(), self._run_freesurfer())
        xnat_job = chain(xnat_job, run_freesurfer)
        xnat_job.apply_async()

    def _add_scans(self, files):
        add_scans = self._add_scan(files[0], first_scan=True)
        if len(files) == 1:
            return add_scans
        else:
            [
                add_scans[i].extend(tasks)
                for file in files[1:]
                for i, tasks in enumerate(self._add_scan(file, first_scan=False))
            ]
            #for file in files[1:]:
                # add_scan_to_xnat, add_scan_to_cloud_storage = self._add_scan(file, first_scan=False)
                # add_scans[0].extend(add_scan_to_xnat)
                # add_scans[1].extend(add_scan_to_cloud_storage)
        return add_scans

    def _add_scan(self, file, first_scan):
        ss = ScanService(self.user, self.experiment)
        do_set_attrs = first_scan and not self.exists_in_xnat
        set_xnat_attrs = self._set_subject_and_experiment_attributes() if do_set_attrs else None
        ss.add_to_database(file, self.xnat_labels, self.existing_labels)
        add_to_xnat = ss.add_to_xnat(first_scan, set_xnat_attrs)
        add_to_cloud_storage = ss.add_to_cloud_storage()
        return [add_to_xnat], [add_to_cloud_storage]


    def _gen_fs_recon_data(self):
        labels = [self.existing_labels[level]['xnat_label'] if len(self.existing_labels[level]['xnat_label']) \
            else self.xnat_labels[level]['xnat_label'] for level in ['subject', 'experiment']]
        return gen_freesurfer_data.s(labels)

    def _get_scans(self):
        scan_ids = [scan.id for scan in self.experiment.scans]
        return group([get_scan_attribute.si('xnat_id', scan_id) for scan_id in scan_ids])

    def _run_freesurfer(self):
        self.ds = DerivationService(self.experiment.scans)
        self.ds.create('freesurfer_recon_all')

        return chain(
            self._gen_fs_recon_data(),
            self.xc.launch_and_poll_for_completion('freesurfer_recon_all'),
            self.ds.update_derivation_model('status', exception_on_failure=True)
        )

    def _set_subject_and_experiment_attributes(self):
        return set_sub_and_exp_xnat_attrs.s(self.xnat_labels, self.user.id, self.experiment.id)



