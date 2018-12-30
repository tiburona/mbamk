# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from flask_security import login_required, login_user, logout_user

from cookiecutter_mbam.public.forms import LoginForm
from cookiecutter_mbam.user.forms import RegisterForm
from cookiecutter_mbam.user.models import User
from cookiecutter_mbam.utils import flash_errors

blueprint = Blueprint('public', __name__, static_folder='../static')

@blueprint.route('/')
def home():
    """ Home page. """
    return render_template('public/home.html')

@blueprint.route('/FAQ')
def FAQ():
    """ FAQ page. """
    return render_template('public/FAQ.html')

@blueprint.route('/about')
def about():
    """ About page. """
    return render_template('public/about.html')

@blueprint.route('/contact')
def contact():
    """ Contact page. """
    return render_template('public/contact.html')

# Uncomment below when set up up blogging app
# @blueprint.route('/community')
# def community():
#     return redirect(url_for('blogging.index'))
