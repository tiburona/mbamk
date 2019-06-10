"""Main application package."""
from cookiecutter_mbam.config import config_by_name, config_name
from celery import Celery

celery = Celery(__name__, broker=config_by_name[config_name].broker_url)
