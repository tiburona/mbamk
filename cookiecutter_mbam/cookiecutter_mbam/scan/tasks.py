from .models import Scan
from cookiecutter_mbam.base_service.tasks import setter_factory, getter_factory, multi_setter_factory
from cookiecutter_mbam import celery

set_attribute = setter_factory(Scan)

set_attributes = multi_setter_factory(Scan)

get_attribute = getter_factory(Scan)

@celery.task
def set_scan_attribute(*args):
    return set_attribute(*args)

@celery.task
def get_scan_attribute(*args):
    return get_attribute(*args)

@celery.task
def set_scan_attributes(*args):
    return set_attributes(*args)








