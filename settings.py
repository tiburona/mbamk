import os

SECRET_KEY='you-will-never-guess'
DEBUG = True

DB_USERNAME = 'spiropan'
DB_PASSWORD = ''
BRAIN_DATABASE_NAME = 'brain_db'
#BRAIN_DATABASE_NAME2 = 'jatos'
DB_HOST = os.getenv('IP','0.0.0.0')
DB_URI = "mysql+pymysql://%s:%s@%s/%s" % (DB_USERNAME, DB_PASSWORD, DB_HOST,BRAIN_DATABASE_NAME)
#DB_URI2 = "mysql+pymysql://%s:%s@%s/%s" % (DB_USERNAME, DB_PASSWORD, DB_HOST,BRAIN_DATABASE_NAME2)
SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = True
#SQLALCHEMY_BINDS = {
#    'jatos':        DB_URI2,
# }


UPLOADED_IMAGES_DEST = '/home/ubuntu/workspace/flask_brain_db/static/images/'
UPLOADED_IMAGES_URL = '/static/images/'
BASEDIR = '/home/ubuntu/workspace/flask_brain_db'

