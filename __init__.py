from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flaskext.markdown import Markdown
from flask_uploads import UploadSet, configure_uploads, IMAGES

app = Flask(__name__)
app.config.from_object('settings')
db = SQLAlchemy(app)

# migrations
migrate = Migrate(app, db)

# Markdown
Markdown(app, extensions=['fenced_code', 'tables'])

# images
uploaded_images = UploadSet('images', 'nii,nii.gz,zip')
configure_uploads(app, uploaded_images)

from user import views
from brain_db import views
from jatos import views



