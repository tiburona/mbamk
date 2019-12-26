"""Main application package."""
from .config import Config as config
from celery import Celery
from cookiecutter_mbam.mbam_logging import app_logger

celery = Celery(__name__,
                broker=config.broker_url,
                backend=config.results_backend)

from cookiecutter_mbam.user import User, Role
from cookiecutter_mbam.scan import Scan
from cookiecutter_mbam.experiment import Experiment
from cookiecutter_mbam.derivation import Derivation
