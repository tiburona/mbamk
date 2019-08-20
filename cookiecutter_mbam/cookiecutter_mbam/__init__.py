"""Main application package."""
from .config import config_by_name, config_name
from celery import Celery
from cookiecutter_mbam.mbam_logging import app_logger

celery = Celery(__name__,
                broker=config_by_name[config_name].broker_url,
                result_backend=config_by_name[config_name].result_backend)

# celery = Celery(__name__, broker=config_by_name[config_name].broker_url)

app_logger.error("celery backend in init file {}".format(celery.backend), extra={'email_admin': False})

