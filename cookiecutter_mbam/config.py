# -*- coding: utf-8 -*-
"""Application configuration
"""
# TODO: Consider wrapping flask db commands with MBAM package so don't have to use fake defaults.
# This will also make the app more secure

from environs import Env

env = Env()
env.read_env()

from flask import current_app

# TODO: Figure out how to remove the debug function in production environments. Spiro will look into Flask
# context processor

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class Config:
    """ Sets default configuration and reads from environment variables for any overwrites"""

    SECRET_KEY = env.str('SECRET_KEY','not-so-secret')
    ENV = env.str('FLASK_ENV', 'development')

    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    WEBPACK_MANIFEST_PATH = 'webpack/manifest.json'

    # Debugging and testing
    DEBUG = env.bool('DEBUG',False) # Be sure the default is False otherwise credentials are exposed in browser
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
    SECURITY_PASSWORD_SALT = env.str('SECURITY_PASSWORD_SALT','not-so-salty')
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_SEND_REGISTER_EMAIL = True
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
    BASIC_AUTH_FORCE = env.bool('BASIC_AUTH_FORCE', False)

    if BASIC_AUTH_FORCE:
        BASIC_AUTH_USERNAME = env.str('BASIC_AUTH_USERNAME')
        BASIC_AUTH_PASSWORD = env.str('BASIC_AUTH_PASSWORD')

    # Mail
    MAIL_USERNAME = env.str('MAIL_USERNAME','foo')
    MAIL_PASSWORD = env.str('MAIL_PASSWORD','bar')
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
    DICOM_TO_NIFTI_COMMAND = int(env.str('DICOM_TO_NIFTI_COMMAND', '1'))
    DICOM_TO_NIFTI_WRAPPER = env.str('DICOM_TO_NIFTI_WRAPPER', 'dcm2niix-xfer')
    FREESURFER_RECON_COMMAND = int(env.str('FREESURFER_RECON_COMMAND', '2'))
    FREESURFER_RECON_WRAPPER = env.str('FREESURFER_RECON_WRAPPER', 'freesurfer-recon-all-xfer')
    FS_TO_MESH_COMMAND = int(env.str('FS_TO_MESH_COMMAND', '3'))
    FS_TO_MESH_WRAPPER = env.str('FS_TO_MESH_WRAPPER', 'fs2mesh-xfer')

    # Cloudfront
    CLOUDFRONT_URL = env.str('CLOUDFRONT_URL','foo')
    CLOUDFRONT_KEY_ID = env.str('CLOUDFRONT_KEY_ID','bar')
    CLOUDFRONT_SECRET_KEY = env.str('CLOUDFRONT_SECRET_KEY','bar')

    # S3
    CLOUD_STORAGE_ACCESS_KEY_ID = env.str('S3_KEY_ID','foo')
    CLOUD_STORAGE_SECRET_ACCESS_KEY = env.str('S3_SECRET_KEY','bar')
    CLOUD_STORAGE_BUCKET_NAME = env.str('S3_BUCKET', 'mbam-test')

    # Celery
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    enable_utc = True
    broker_url = env.str('BROKER_URL', 'redis://localhost:6379')
    results_backend = env.str('RESULTS_BACKEND', broker_url)
