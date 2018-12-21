"""Settings module for test app."""
ENV = 'development'
TESTING = True
SQLALCHEMY_DATABASE_URI = 'sqlite://'
SECRET_KEY = 'not-so-secret-in-tests'
#BCRYPT_LOG_ROUNDS = 4  # For faster tests; needs at least 4 to avoid "ValueError: Invalid rounds"
DEBUG_TB_ENABLED = False
CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False
WEBPACK_MANIFEST_PATH = 'webpack/manifest.json'
WTF_CSRF_ENABLED = False  # Allows form testing

PRESERVE_CONTEXT_ON_EXCEPTION = False
SECURITY_PASSWORD_SALT = 'test'
SECURITY_PASSWORD_HASH='bcrypt'
SECURITY_EMAIL_SUBJECT_REGISTER = 'Welcome to MyBrainandMe!'

# Flask-Mail Settings
MAIL_USERNAME = 'mbaminfo@gmail.com'
#MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_PASSWORD = 'vcncnzonsvblmjpb'
MAIL_DEFAULT_SENDER = '"MyBrainandMe" <mbaminfo@gmail.com>'
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_SSL = False
MAIL_USE_TLS = True
