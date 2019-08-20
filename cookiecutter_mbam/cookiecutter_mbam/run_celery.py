from cookiecutter_mbam.app import create_app
from cookiecutter_mbam import celery
from cookiecutter_mbam.init_celery import init_celery
from .config import config_by_name, config_name

print(config_name)

app = create_app(config_name)
init_celery(app, celery)
