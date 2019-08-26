"""Main application package."""
from .config import config_by_name, config_name
from celery import Celery
from cookiecutter_mbam.mbam_logging import app_logger

celery = Celery(__name__,
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/1')




