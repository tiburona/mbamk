from .models import Experiment
from cookiecutter_mbam.base_service.tasks import setter_factory, getter_factory
from cookiecutter_mbam import celery

set_attribute = setter_factory(Experiment)

get_attribute = getter_factory(Experiment)

@celery.task
def set_experiment_attribute(*args):
    return set_attribute(*args)

@celery.task
def get_experiment_attribute(*args):
    return get_attribute(*args)