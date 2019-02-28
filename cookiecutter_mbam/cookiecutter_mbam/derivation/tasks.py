from .models import Derivation

from celery.signals import task_prerun
from flask import g


# from cookiecutter_mbam.app import make_celery
# celery = make_celery()

from cookiecutter_mbam import celery


@celery.task
def update_status_on_derivation_model(status, model_id):
    derivation = Derivation.get_by_id(model_id)
    derivation.update(status=status)
    return status