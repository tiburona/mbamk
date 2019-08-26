from .models import Scan
from celery import group
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery


set_attribute, set_attributes, get_attribute = run_task_factories(Scan)

@celery.task
def set_scan_attribute(*args):
    return set_attribute(*args)

@celery.task
def get_scan_attribute(*args):
    return get_attribute(*args)

@celery.task
def set_scan_attributes(*args):
    return set_attributes(*args)










