from .models import Derivation

from cookiecutter_mbam import celery


@celery.task
def update_derivation_model(val, model_id, key):
    derivation = Derivation.get_by_id(model_id)
    args = {key: val}
    derivation.update(**args)
    return val