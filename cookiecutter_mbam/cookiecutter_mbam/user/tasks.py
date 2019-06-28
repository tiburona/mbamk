from .models import User
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery

set_attribute, set_attributes, get_attribute = run_task_factories(User)

@celery.task
def set_user_attribute(*args):
    return set_attribute(*args)

@celery.task
def get_user_attribute(*args):
    return get_attribute(*args)