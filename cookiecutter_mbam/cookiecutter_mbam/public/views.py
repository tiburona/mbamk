# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint, flash, redirect, render_template, url_for, current_app

from cookiecutter_mbam.utils.error_utils import flash_errors
from flask_security import current_user
from cookiecutter_mbam.public.forms import ContactForm
from cookiecutter_mbam.user.forms import ProfileForm


blueprint = Blueprint('public', __name__, static_folder='../static')

@blueprint.route('/')
def home():
    """ Home page. """
    if current_user.is_authenticated:
        if current_user.sex or current_user.dob or current_user.first_name or current_user.last_name:
            action="edit"
        else:
            action="create"

        form=ProfileForm(obj=current_user)
        if form.validate_on_submit():
            form.populate_obj(current_user)
            current_user.save()
            flash('User profile saved.','success')
            return redirect(url_for('public.home'))
        else:
            flash_errors(form)
    else:
        form=None
        action=None

    return render_template('public/home.html', profile_form=form, action=action)

@blueprint.route('/FAQ')
def FAQ():
    """ FAQ page. """
    return render_template('public/FAQ.html')

@blueprint.route('/about')
def about():
    """ About page. """
    return render_template('public/about.html')

@blueprint.route('/media')
def media():
    """ Media page. """
    return render_template('public/media.html')

@blueprint.route('/team')
def team():
    """ Team page. """
    return render_template('public/team.html')

@blueprint.route('/contact', methods=('GET','POST'))
def contact():
    """ Contact page. """
    form = ContactForm()
    if form.validate_on_submit():
        # Come back to this and complete. Write or use function for sending email
        flash('Message sent. Thank you for contacting us.','success')
        return redirect(url_for('public.home'))

    return render_template('public/contact.html',contact_form=form)

# Uncomment below when set up up blogging app
# @blueprint.route('/community')
# def community():
#     return redirect(url_for('blogging.index'))
