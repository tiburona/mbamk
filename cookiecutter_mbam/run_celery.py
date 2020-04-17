from cookiecutter_mbam.app import create_app
from cookiecutter_mbam import celery
from cookiecutter_mbam.init_celery import init_celery

app = create_app()
init_celery(app, celery)
