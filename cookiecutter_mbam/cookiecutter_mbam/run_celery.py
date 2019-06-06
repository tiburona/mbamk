from cookiecutter_mbam.app import create_app
from cookiecutter_mbam import celery
from cookiecutter_mbam.init_celery import init_celery

app = create_app(config_object='cookiecutter_mbam.settings')
init_celery(app, celery)


