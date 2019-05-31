from .models import Derivation
from cookiecutter_mbam.base_service.tasks import setter_factory, getter_factory
from cookiecutter_mbam import celery


set_attribute = setter_factory(Derivation)

get_attribute = getter_factory(Derivation)

@celery.task
def set_derivation_attribute(*args):
    return set_attribute(*args)

@celery.task
def get_derivation_attribute(*args):
    return get_attribute(*args)

@celery.task
def raise_exception(val, whitelist=None, blacklist=None):
    if whitelist:
        if val not in whitelist:
            raise ValueError(f'Not allowed: {val}\nAcceptable values:{whitelist}')
    if blacklist:
        if val in blacklist:
            raise ValueError(f'Disallowed: {val}\nUncceptable values:{blacklist}')
    return val




