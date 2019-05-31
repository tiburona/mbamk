from .models import User
from cookiecutter_mbam.base_service.tasks import setter_factory, getter_factory
from cookiecutter_mbam import celery

set_attribute = setter_factory(User)

get_attribute = getter_factory(User)

@celery.task
def set_user_attribute(*args):
    return set_attribute(*args)

@celery.task
def get_user_attribute(*args):
    return get_attribute(*args)