# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from environs import Env

env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'
SQLALCHEMY_DATABASE_URI = env.str('DATABASE_URL')
SECRET_KEY = env.str('SECRET_KEY')
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
SECURITY_EMAIL_SENDER = '"MyBrainandMe" <mbaminfo@gmail.com>'
SECURITY_REGISTERABLE = True

# Flask-Mail Settings
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
