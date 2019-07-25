# -*- coding: utf-8 -*-
"""Application configuration.
Module defining classes for configuring the app across multiple environments.
Based loosely on https://medium.freecodecamp.org/structuring-a-flask-restplus-web-service-for-production-builds-c2ec676de563
At the bottom is the config_name which sets the app environment passed on to application factory.
"""

from environs import Env
import os
env = Env()
env.read_env()

class Config:
    """ Base config class the sets variables in common (or default) to all environments."""
    SECRET_KEY = env.str('SECRET_KEY')
    ENV = env.str('FLASK_ENV', default='production')
    DEBUG = ENV == 'development'

    DEBUG_TB_ENABLED = DEBUG
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    WEBPACK_MANIFEST_PATH = 'webpack/manifest.json'

    # Flask security settings
    SECURITY_PASSWORD_SALT = 'super-secret-random-salt' # erm, keep out of our repo in real prod version?
    SECURITY_PASSWORD_HASH='bcrypt'
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_EMAIL_SENDER = '"My Brain and Me" <mbaminfo@gmail.com>'
    SECURITY_REGISTERABLE = True
    SECURITY_CHANGEABLE = True

    # Flask-Mail Settings
    #MAIL_USERNAME = 'testingmbam@gmail.com'
    #MAIL_PASSWORD='R8S6bSgeqGgknH3'
    MAIL_USERNAME = 'mbaminfo@gmail.com'
    # Below is temporary application specific password for gmail smtp. Delete and replace with
    # env variable when repo goes public
    MAIL_PASSWORD='digkexrwzscfpybx'
    # Wait for the fix in flask-security, see https://github.com/mattupstate/flask-security/issues/685
    #MAIL_DEFAULT_SENDER = '"MyBrainandMe" <mbaminfo@gmail.com>'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True

    # File upload settings
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024

    # Logging Settings
    LOG_FILENAME = 'static/logs/log.txt'

    # Celery settings
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    enable_utc = True

    include = ['cookiecutter_mbam.xnat.tasks', 'cookiecutter_mbam.storage.tasks', 'cookiecutter_mbam.derivation.tasks',
               'cookiecutter_mbam.scan.tasks', 'cookiecutter_mbam.base.tasks']

    XNAT = {
        'user': 'admin',
        'password': 'admin',
        'server': 'http://10.1.1.17',
        'project': 'MBAM_TEST',
        'local_docker': True,
        'docker_host': 'unix:///var/run/docker.sock',
        'dicom_to_nifti_command_id': 2,
        'dicom_to_nifti_wrapper_id':'dcm2niix-scan',
        'dicom_to_nifti_transfer_command_id':3,
        'dicom_to_nifti_transfer_wrapper_id':'dcm2niix-xfer'
    }

    files = {
        'file_depot': 'static/files/',
        'file_depot_url': 'http://0.0.0.0:8081/static/files/'
    }

    AWS = {
        'access_key_id': 'AKIAJ3CJ3JWENS3XA6QQ',
        'secret_access_key': '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',
        'bucket_name' : 'mbam-test'
    }


class LocalConfig(Config):
    """ Class defining configurations for local development. Config_name is 'local'. """
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/dev.db'

    # Default settings for Flask-Security
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_CONFIRMABLE = False

    # Celery local settings
    broker_url = 'redis://localhost:6379'
    result_backend = 'redis://localhost:6379'

class DockerConfig(Config):
    """ Class defining configurations for local development. Config_name is 'docker'. """
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mbam:mbam123@mysql/brain_db'
    # Celery cettings
    broker_url = 'redis://redis:6379'
    result_backend = 'redis://redis:6379'

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 'not-so-secret-in-tests'
    DEBUG_TB_ENABLED = False
    WTF_CSRF_ENABLED = False  # Allows form testing
    PRESERVE_CONTEXT_ON_EXCEPTION = False

class DevConfig(Config):
    """ Class defining configurations for local development. Config_name is 'aws_dev'. """
    DB_URI = env.str('DB_URI')
    DB_USER = env.str('DB_USER', default='mbam')
    DB_PASSWORD = env.str('DB_PASSWORD', default='mbam1234')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}/brain_db'.format(DB_USER,DB_PASSWORD,DB_URI)

    # Celery cettings COME BACK TO
    broker_url = 'redis://redis:6379'
    result_backend = 'redis://redis:6379'

config_by_name = dict(
    local=LocalConfig,
    docker=DockerConfig,
    test=TestConfig,
    aws_dev=DevConfig
    )

def guess_environment():
    """ This function will guess the config_name. The value can be overridden at the bottom of this file.

    :returns config_name: String specifying the configuration.
    """
    # Override the configuration with an environment variable if it's set
    config_name = os.getenv('CONFIG_NAME')

    # If configuration is not set in the
    if not config_name:
        if os.uname()[1].find('Mac') > -1:
            config_name='local'
        else:
            config_name='docker'

    return config_name

# Guess the config_names for dev and testing configurations
config_name = guess_environment()
