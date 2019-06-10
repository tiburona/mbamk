from cookiecutter_mbam.app import create_app
from cookiecutter_mbam import celery
from cookiecutter_mbam.init_celery import init_celery
from cookiecutter_mbam.config import config_name

app = create_app(config_name=config_name)
init_celery(app, celery)
