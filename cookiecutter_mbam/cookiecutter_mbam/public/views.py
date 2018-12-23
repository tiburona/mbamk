# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from flask_security import login_required, login_user, logout_user

from cookiecutter_mbam.public.forms import LoginForm
from cookiecutter_mbam.user.forms import RegisterForm
from cookiecutter_mbam.user.models import User
from cookiecutter_mbam.utils import flash_errors

blueprint = Blueprint('public', __name__, static_folder='../static')

@blueprint.route('/', methods=['GET', 'POST'])
def home():
    """Home page."""
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            flash('You are logged in.', 'success')
            redirect_url = request.args.get('next') or url_for('user.members')
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template('public/home.html', form=form)


# @blueprint.route('/logout/')
# @login_required
# def logout():
#     """Logout."""
#     logout_user()
#     flash('You are logged out.', 'info')
#     return redirect(url_for('public.home'))


# @blueprint.route('/register/', methods=['GET', 'POST'])
# def register():
#     """Register new user."""
#     form = RegisterForm(request.form)
#     if form.validate_on_submit():
#         User.create(email=form.email.data, password=form.password.data, active=True)
#         flash('Thank you for registering. You can now log in.', 'success')
#         return redirect(url_for('public.home'))
#     else:
#         flash_errors(form)
#     return render_template('public/register.html', form=form)


@blueprint.route('/about/')
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template('public/about.html', form=form)
