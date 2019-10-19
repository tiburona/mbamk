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
    ENV = env.str('FLASK_ENV', default='development')
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
        # Be sure below XNAT variables are set in your host environment to access the MIND XNAT server.
        # Default values assume you are using a local VM XNAT
        'user': env.str('XNAT_USER','admin'),
        'password': env.str('XNAT_PASSWORD','admin'),
        'server': env.str('XNAT_HOST','http://10.1.1.17'),
        'project': env.str('XNAT_PROJECT', 'MBAM_TEST'),
        'local_docker': False,
        'docker_host': env.str('XNAT_DOCKER_HOST','unix:///var/run/docker.sock'),
        'dicom_to_nifti_command_id': 1, # DEPRECATED
        'dicom_to_nifti_wrapper_id':'dcm2niix-scan', # DEPRECATED
        'dicom_to_nifti_transfer_command_id': env.int('DICOM_TO_NIFTI_TRANSFER_COMMAND_ID',2),
        'dicom_to_nifti_transfer_wrapper_id':'dcm2niix-xfer',
        'freesurfer_recon_all_transfer_command_id': env.str('FREESURFER_RECON', default='15'),
        'freesurfer_recon_all_transfer_wrapper_id': 'freesurfer-recon-all-xfer'
    }

    files = {
        'file_depot': 'static/files/', # this corresponds to /app/static/files ContainerMountPoint
        'file_depot_url': 'http://0.0.0.0:8081/static/files/'
    }

    AWS = {
        # Grab variables from environment. Default are Katie's dev params
        'access_key_id': env.str('AWS_KEY_ID','AKIAJ3CJ3JWENS3XA6QQ'),
        'secret_access_key': env.str('AWS_SECRET_KEY','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'),
        'bucket_name' : env.str('AWS_S3_BUCKET','mbam-test'),
        # Below the default values are default cloudfront dev params set up for Spiro's AWS account
        'cloudfront_url' : env.str('CLOUDFRONT_URL','https://dc2khv0msnx9b.cloudfront.net/'),
        'cloudfront_key_id' : env.str('CLOUDFRONT_KEY_ID','APKAJZ3J6OMQJKG2PO4Q'),
        'cloudfront_private_key' : env.str('CLOUDFRONT_PRIVATE_KEY', default='none')
    }

class LocalConfig(Config):
    """ Class defining configurations for local development. Config_name is 'local'. """
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/dev.db'

    # Default settings for Flask-Security
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_CONFIRMABLE = False

    # Celery local settings
    broker_url = 'redis://localhost:6379'
    results_backend = broker_url

class DockerConfig(Config):
    """ Class defining configurations for docker development. Config_name is 'docker'. This is the
    environment used for build testing in SemaphoreCI"""
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mbam:mbam123@mysql/brain_db'
    # Celery cettings
    broker_url = 'redis://redis:6379'
    results_backend = 'redis://redis:6379'

    XNAT=Config.XNAT
    XNAT['dicom_to_nifti_transfer_command_id'] = env.int('DICOM_TO_NIFTI_TRANSFER_COMMAND_ID',23)
    XNAT['docker_host'] = env.str('XNAT_DOCKER_HOST','http://10.20.193.32:2375')

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 'not-so-secret-in-tests'
    DEBUG_TB_ENABLED = False
    WTF_CSRF_ENABLED = False  # Allows form testing
    PRESERVE_CONTEXT_ON_EXCEPTION = False

class DevConfig(Config):
    """ Class defining configurations for development on AWS. Config_name is 'staging'. """
    # MYSQL parameters are stored in AWS Systems Manager Parameter store and passed
    # as environment variables in the Cloudformation Templates.
    DB_URI = env.str('MYSQL_HOST','dummy')
    DB_USER = env.str('MYSQL_USERNAME','dummy')
    DB_PASSWORD = env.str('MYSQL_PASSWORD','dummy')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}/brain_db'.format(DB_USER,DB_PASSWORD,DB_URI)

    # Celery settings. App will connect to redis memcache set up in AWS
    broker_url = env.str('broker_url', default='dummy')
    results_backend = broker_url

    XNAT=Config.XNAT
    XNAT['dicom_to_nifti_transfer_command_id'] = env.int('DICOM_TO_NIFTI_TRANSFER_COMMAND_ID',23)
    XNAT['project'] = env.str('XNAT_PROJECT', 'MBAM_STAGING')
    XNAT['docker_host'] = env.str('XNAT_DOCKER_HOST','http://10.20.193.32:2375')

    # Protect the staging server until the site goes live
    BASIC_AUTH_USERNAME='tester'
    BASIC_AUTH_PASSWORD='mind@nyspi'
    BASIC_AUTH_FORCE=True

config_by_name = dict(
    local=LocalConfig,
    docker=DockerConfig,
    test=TestConfig,
    staging=DevConfig
    )

def guess_environment():
    """ This function will guess the config_name. The value can be overridden at the bottom of this file.

    :returns config_name: String specifying the configuration.
    """
    # Override the configuration with an environment variable if it's set in the .env file
    try:
        config_name = env.str('CONFIG_NAME')
    except:
        if os.uname()[1].find('Mac') > -1:
            config_name='local'
        elif os.uname()[1].find('ip-') > -1:
            config_name='staging'
        else:
            config_name='docker'

    return config_name

# Guess the config_names for dev and testing configurations
config_name = guess_environment()
