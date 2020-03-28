"""Settings module for test app."""
ENV = 'development'
TESTING = True
SQLALCHEMY_DATABASE_URI = 'sqlite://'
SECRET_KEY = 'not-so-secret-in-tests'
DEBUG_TB_ENABLED = False
CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False
WEBPACK_MANIFEST_PATH = 'webpack/manifest.json'
WTF_CSRF_ENABLED = False  # Allows form testing

PRESERVE_CONTEXT_ON_EXCEPTION = False
SECURITY_PASSWORD_SALT = 'test'
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_EMAIL_SUBJECT_REGISTER = 'Welcome to My Brain and Me!'
SECURITY_EMAIL_SENDER = '"MyBrainandMe" <mbaminfo@gmail.com>'
SECURITY_REGISTERABLE = True

# Flask-Mail Settings
MAIL_USERNAME = 'mbaminfo@gmail.com'
# Below is temporary application specific password for gmail smtp. Delete and replace with
# env variable when repo goes public
MAIL_PASSWORD='digkexrwzscfpybx'
MAIL_DEFAULT_SENDER = '"My Brain and Me" <mbaminfo@gmail.com>'
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_SSL = False
MAIL_USE_TLS = True
