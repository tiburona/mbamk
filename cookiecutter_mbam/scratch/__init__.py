from celery import Celery
from .config import LocalConfig

celery = Celery(__name__,
                broker=LocalConfig.broker_url,
                result_backend=LocalConfig.result_backend)