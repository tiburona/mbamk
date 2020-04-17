from .models import Derivation
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery
import os

set_attribute, set_attributes, get_attribute = run_task_factories(Derivation)

@celery.task
def set_derivation_attribute(*args):
    return set_attribute(*args)

@celery.task
def get_derivation_attribute(*args):
    return get_attribute(*args)

@celery.task
def set_derivation_attributes(*args):
    return set_attributes(*args)

@celery.task
def raise_exception(val, whitelist=None, blacklist=None):
    if whitelist:
        if val not in whitelist:
            raise ValueError(f'Not allowed: {val}\nAcceptable values:{whitelist}')
    if blacklist:
        if val in blacklist:
            raise ValueError(f'Disallowed: {val}\nUncceptable values:{blacklist}')
    return val

@celery.task
def construct_derivation_uri_from_scan_uri(derivation_id, suffix):
    derivation = Derivation.get_by_id(derivation_id)
    scan_uri = derivation.scans[0].xnat_uri
    return scan_uri + suffix





