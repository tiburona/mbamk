# -*- coding: utf-8 -*-
"""Application configuration
"""

from environs import Env

env = Env()
env.read_env()

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class Config:
    """ Sets default configuration and reads from environment variables for any overwrites"""


    SECRET_KEY = env.str('SECRET_KEY')
    ENV = env.str('FLASK_ENV', 'development')

    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    WEBPACK_MANIFEST_PATH = 'webpack/manifest.json'

    # Debugging and testing

    DEBUG = True
    TESTING = env.bool('TESTING', False)
    WTF_CSRF_ENABLED = env.bool('WTF_CSRF_ENABLED', True)
    DEBUG_TB_ENABLED = env.bool('DEBUG_TB_ENABLED', DEBUG)
    PRESERVE_CONTEXT_ON_EXCEPTION = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False


    # Server

    default_server = None if ENV == 'test' else '0.0.0.0:8000'
    
    SERVER_NAME = env.str('SERVER_NAME', default_server)
    PREFERRED_URL_SCHEME = env.str('PREFFERED_URL_SCHEME', 'http')


    # Flask security

    SECURITY_PASSWORD_SALT = env.str('SECURITY_PASSWORD_SALT')
    SECURITY_PASSWORD_HASH='bcrypt'
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_EMAIL_SENDER = env.str('SECURITY_EMAIL_SENDER', '"My Brain and Me" <mbaminfo@gmail.com>')

    # File upload
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024
    FILE_DEPOT = 'static/files/'

    # Database

    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DB_URI = env.str('MYSQL_HOST', 'localhost')
    DB_USER = env.str('MYSQL_USERNAME', 'mbam')
    DB_PASSWORD = env.str('MYSQL_PASSWORD', 'mbam123')
    SQLALCHEMY_DATABASE_URI = env.str('SQLALCHEMY_DATABASE_URI',
                                      'mysql+pymysql://{}:{}@{}/brain_db'.format(DB_USER, DB_PASSWORD, DB_URI))

    # Auth

    BASIC_AUTH_USERNAME = ''
    BASIC_AUTH_PASSWORD = ''
    BASIC_AUTH_FORCE = False

    # Mail

    MAIL_USERNAME = env.str('MAIL_USERNAME')
    MAIL_PASSWORD = env.str('MAIL_PASSWORD')
    MAIL_SERVER = env.str('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = env.int('MAIL_PORT', 587)
    MAIL_USE_SSL = env.bool('MAIL_USE_SSL', False)
    MAIL_USE_TLS = env.bool('MAIL_USE_TLS', True)

    # XNAT

    XNAT_HOST = env.str('XNAT_HOST', 'http://10.1.1.17')
    XNAT_USER = env.str('XNAT_USER', 'admin')
    XNAT_PASSWORD = env.str('XNAT_PASSWORD', 'admin')
    XNAT_DOCKER_HOST = env.str('XNAT_DOCKER_HOST','unix:///var/run/docker.sock')
    XNAT_PROJECT = env.str('XNAT_PROJECT', 'MBAM_TEST')
    DICOM_TO_NIFTI_COMMAND = int(env.str('DICOM_TO_NIFTI_COMMAND'))
    DICOM_TO_NIFTI_WRAPPER = env.str('DICOM_TO_NIFTI_WRAPPER', 'dcm2niix-xfer')
    FREESURFER_RECON_COMMAND = int(env.str('FREESURFER_RECON_COMMAND'))
    FREESURFER_RECON_WRAPPER = env.str('FREESURFER_RECON_WRAPPER', 'freesurfer-recon-all-xfer')


    # Cloudfront

    CLOUDFRONT_URL = env.str('CLOUDFRONT_URL')
    CLOUDFRONT_KEY_ID = env.str('CLOUDFRONT_KEY_ID')
    CLOUDFRONT_SECRET_KEY = env.str('CLOUDFRONT_SECRET_KEY')


    # S3

    CLOUD_STORAGE_ACCESS_KEY_ID = env.str('S3_KEY_ID')
    CLOUD_STORAGE_SECRET_ACCESS_KEY = env.str('S3_SECRET_KEY')
    CLOUD_STORAGE_BUCKET_NAME = env.str('S3_BUCKET', 'mbam-test')


    # Celery

    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    enable_utc = True
    broker_url = env.str('BROKER_URL', 'redis://localhost:6379')
    results_backend = env.str('RESULTS_BACKEND', broker_url)





