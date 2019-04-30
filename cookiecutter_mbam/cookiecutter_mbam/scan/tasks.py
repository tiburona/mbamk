from .models import Scan
from cookiecutter_mbam.derivation import Derivation
from cookiecutter_mbam.experiment import Experiment
from cookiecutter_mbam.user import User

from cookiecutter_mbam import celery

class_names = {
    'scan' : Scan,
    'user' : User,
    'derivation' : Derivation,
    'experiment' : Experiment
}


@celery.task
def update_database_objects(uris=[], model_names=[], model_ids = [], keywords=[], xnat_ids=[]):
    attributes = zip(model_names, model_ids, keywords, uris, xnat_ids)
    for (model_name, model_id, kw, uri, id) in attributes:
        obj = class_names[model_name].get_by_id(model_id)
        obj.update(xnat_uri=uri)
        obj.update(**{'xnat_{}_id'.format(kw): id})


