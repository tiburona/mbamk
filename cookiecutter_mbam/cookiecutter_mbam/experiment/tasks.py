from .models import Experiment
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery as cel
from celery import group
from cookiecutter_mbam.scan.tasks import get_scan_attribute

set_attribute, set_attributes, get_attribute = run_task_factories(Experiment)

@cel.task
def set_experiment_attribute(*args):
    return set_attribute(*args)

@cel.task
def get_experiment_attribute(*args):
    return get_attribute(*args)

@cel.task
def get_scan_xnat_ids(scan_ids):
    return group([get_scan_attribute.s('xnat_id', scan_id) for scan_id in scan_ids])()

@cel.task
def gen_fs_recon_data(exp_id, scan_ids):
    scan_xnat_ids = group([get_scan_attribute.s('xnat_id', scan_id) for scan_id in scan_ids])()
    experiment_xnat_id = get_experiment_attribute.s('xnat_id', exp_id)()
    return {
            'scans': ' '.join(scan_xnat_ids),
            'experiment_id': experiment_xnat_id
        }


