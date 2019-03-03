from .models import Derivation

from cookiecutter_mbam import celery


@celery.task
def update_derivation_model(model_id, **args):
    derivation = Derivation.get_by_id(model_id)
    derivation.update(**args)
    return args.values()[0]