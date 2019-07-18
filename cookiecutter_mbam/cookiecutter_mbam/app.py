# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
from flask import Flask, render_template
import cookiecutter_mbam.logging
from flask_security import SQLAlchemyUserDatastore
from celery import Celery
from cookiecutter_mbam import celery
from cookiecutter_mbam.init_celery import init_celery
from cookiecutter_mbam import commands, public, user, experiment, scan
from cookiecutter_mbam.admin import UserAdmin, RoleAdmin
from cookiecutter_mbam.extensions import admin, cache, csrf_protect, db, debug_toolbar, migrate, \
    security, webpack, mail, jsglue
from cookiecutter_mbam.user import User, Role
from .hooks import create_test_users, models_committed_hooks
from .config import config_by_name, config_name

def create_app(config_name=config_name):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.
    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_by_name[config_name])

    init_celery(app, celery=celery)
    register_extensions(app)
    register_hooks(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    return app

def register_extensions(app):
    """Register Flask extensions."""
    cache.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, datastore=user_datastore)
    create_test_users(app, user_datastore, db)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    webpack.init_app(app)
    admin.init_app(app, endpoint='admin')
    mail.init_app(app)
    jsglue.init_app(app)
    return None

def register_hooks(app):
    """Register hooks"""
    models_committed_hooks(app)

def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(experiment.views.blueprint)
    app.register_blueprint(scan.views.blueprint)
    return None

def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 413, 500]:
        app.errorhandler(errcode)(render_error)
    return None

def register_shellcontext(app):
    """Register shell context objects."""
    # TODO: Add other models here.
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User}

    app.shell_context_processor(shell_context)

def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)

def register_admin_views():
    """Register Flask admin views."""
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(RoleAdmin(Role, db.session))

def make_celery(app=None):
    app = app or create_app(config_name=config_name)
    celery = Celery(__name__, broker=config_by_name[config_name].broker_url)
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
