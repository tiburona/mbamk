from flask import Flask
from scratch import celery
from .init_celery import init_celery

from .config import LocalConfig, config_by_name, config_name

def create_app():
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    init_celery(app, celery=celery)

    return app
