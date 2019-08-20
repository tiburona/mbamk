from .models import Experiment
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery

set_attribute, set_attributes, get_attribute = run_task_factories(Experiment)

@celery.task
def set_experiment_attribute(*args):
    return set_attribute(*args)

@celery.task
def get_experiment_attribute(*args):
    return get_attribute(*args)


