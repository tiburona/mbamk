# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_security import Security
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_webpack import Webpack
from flask_wtf.csrf import CSRFProtect
from flask_admin import Admin
from flask_mail import Mail
from flask_jsglue import JSGlue
from flask_basicauth import BasicAuth # To protect the staging server until it goes live

admin = Admin()
csrf_protect = CSRFProtect()
db = SQLAlchemy()
security = Security()
migrate = Migrate()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
webpack = Webpack()
mail = Mail()
jsglue = JSGlue()
basicauth = BasicAuth()
