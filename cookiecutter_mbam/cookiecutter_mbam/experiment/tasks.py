from .models import Experiment
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery as cel
from celery import group
from cookiecutter_mbam.scan.tasks import get_scan_attribute
from cookiecutter_mbam.user.tasks import set_attributes as set_subject_attributes

set_attribute, set_attributes, get_attribute = run_task_factories(Experiment)

@cel.task
def set_experiment_attribute(*args):
    return set_attribute(*args)

@cel.task
def get_experiment_attribute(*args):
    return get_attribute(*args)

@cel.task
def set_experiment_attributes(*args):
    return set_attributes(*args)

@cel.task
def get_scan_xnat_ids(scan_ids):
    return group([get_scan_attribute.s('xnat_id', scan_id) for scan_id in scan_ids])()

@cel.task
def gen_freesurfer_data(scan_ids, sub_and_exp_ids):
    sub_id, exp_id = sub_and_exp_ids
    return {
        'scans': scan_ids,
        'experiment': exp_id,
        'subject': sub_id
    }

@cel.task
def set_sub_and_exp_xnat_attrs(responses, xnat_labels, user_id, exp_id):
    sub, exp = [{'xnat_id': responses[key],
                 'xnat_uri': '/data/experiments/{}'.format(responses[key]),
                 'xnat_label': xnat_labels[key]['xnat_label']}
                for key in ['subject', 'experiment']]
    set_subject_attributes(sub, user_id)
    set_experiment_attributes(exp, exp_id)

