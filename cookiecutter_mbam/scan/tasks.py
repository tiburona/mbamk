import os
import zipfile
from .models import Scan
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery as cel

set_attribute, set_attributes, get_attribute = run_task_factories(Scan)

@cel.task
def set_scan_attribute(*args):
    return set_attribute(*args)

@cel.task
def get_scan_attribute(*args):
    return get_attribute(*args)

@cel.task
def set_scan_attributes(*args):
    return set_attributes(*args)



