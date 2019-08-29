from celery import Celery
from .config import LocalConfig

celery = Celery(__name__,
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/1')