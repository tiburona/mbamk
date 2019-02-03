# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_security import login_required, current_user
from .forms import ProfileForm, ConsentForm, AssentForm
from cookiecutter_mbam.utils import flash_errors

blueprint = Blueprint('user', __name__, url_prefix='/users', static_folder='../static')

@blueprint.route('/')
@login_required
def members():
    """List members."""
    return render_template('users/members.html')

@blueprint.route('/profile', methods=('GET','POST'))
@login_required
def profile():
    """ Basic user profile form """
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        current_user.save()
        flash('User profile saved','success')
        return redirect(url_for('user.consent'))
    else:
        flash_errors(form)

    return render_template('users/profile.html', form=form)

@blueprint.route('/consent', methods=('GET','POST'))
@login_required
def consent():
    """ Consent form for participation in research."""
    form = ConsentForm()
    if form.validate_on_submit():
        current_user.update(consented=form.consented.data)
        if current_user.consented:
            flash('Consent for participation in research provided','success')
            return redirect(url_for('scan.add_experiment_and_scans'))
        else:
            flash('Consent for participation in research NOT provided','alert')
            return redirect(url_for('pubic.home'))

    return render_template('users/consent.html',form=form)

@blueprint.route('/assent', methods=('GET','POST'))
@login_required
def assent():
    """ Assent form for participation in research."""
    form = AssentForm()
    if form.validate_on_submit():
        current_user.update(assented=form.assented.data)
        if current_user.assented:
            flash('Assent for participation in research provided','success')
            return redirect(url_for('scan.add_experiment_and_scans'))
        else:
            flash('Assent for participation in research NOT provided','alert')
            return redirect(url_for('pubic.home'))

    return render_template('users/assent.html',form=form)

@blueprint.route('/parent_permission', methods=('GET','POST'))
@login_required
def parent_permission():
    """ Parent permission form for participation in research."""
    form = ConsentForm()
    if form.validate_on_submit():
        current_user.update(consented=form.consented.data)
        if current_user.consented:
            flash('Consent for participation in research provided','success')
            return redirect(url_for('scan.add_experiment_and_scans'))
        else:
            flash('Consent for participation in research NOT provided','alert')
            return redirect(url_for('pubic.home'))

    return render_template('users/parent_permission.html',form=form)
