# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_security import login_required, current_user

from cookiecutter_mbam.utils.error_utils import flash_errors
from .forms import ProfileForm, ConsentForm, AssentForm

blueprint = Blueprint('user', __name__, url_prefix='/users', static_folder='../static')


def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

@blueprint.route('/')
def home():
    """ Members page. """
    return render_template('users/members.html')


@blueprint.route('/profile', methods=('GET','POST'))
@login_required
def profile():
    """ Basic user profile form """
    if current_user.sex or current_user.dob or current_user.first_name or current_user.last_name:
        action="edit"
    else:
        action="create"

    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        current_user.save()
        flash('User profile saved','success')
        return redirect(url_for('public.home'))
    else:
        flash_errors(form)

    return render_template('users/profile.html', form=form, action=action)

@blueprint.route('/consent', methods=('GET','POST'))
@login_required
def consent():
    """ Consent form for participation in research."""
    if isinstance(current_user.sex,str): # Check if user profile was filled out
        form = ConsentForm()
        if form.validate_on_submit():
            current_user.update(consented=form.consented.data)
            flash('User consent provided','success')
            return redirect(url_for('experiment.add'))
    else:
        # Is user profile is not completed, direct the user to the form
        flash('Please fill out a user profile first','success')
        return redirect(url_for('user.profile'))

    return render_template('users/consent.html',form=form)

@blueprint.route('/assent', methods=('GET','POST'))
@login_required
def assent():
    """ Assent form for participation in research."""
    form = AssentForm()
    if form.validate_on_submit():
        current_user.update(assented=form.assented.data, parent_email=form.email.data)
        if current_user.assented:
            flash('Assent provided. Please have your parent or legal guardian consent.','success')
            return redirect(url_for('public.home'))
        else:
            flash('Assent NOT provided','alert')
            return redirect(url_for('public.home'))

    return render_template('users/assent.html',form=form)

@blueprint.route('/parent_permission', methods=('GET','POST'))
@login_required
def parent_permission():
    """ Parent permission form for participation in research."""
    form = ConsentForm()
    if form.validate_on_submit():
        # Come back and add code here to find children of parent and call the object
        # minor
        if current_user.consented:
            flash('Parent permission provided','success')
            return redirect(url_for('experiment.add'))
        else:
            flash('Parent permission NOT provided','alert')
            return redirect(url_for('public.home'))

    return render_template('users/parent_permission.html',form=form)
