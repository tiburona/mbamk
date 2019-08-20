# -*- coding: utf-8 -*-
"""Experiment views."""

import traceback
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_security import current_user

from cookiecutter_mbam.utils.error_utils import flash_errors
from .forms import ExperimentForm, ExperimentAndScanForm
from .models import Experiment
from .service import ExperimentService
from cookiecutter_mbam.scan import ScanService
from cookiecutter_mbam.base.tasks import global_error_handler

blueprint = Blueprint('experiment', __name__, url_prefix='/experiments', static_folder='../static')

def add_experiment(form, files):
    """Add an experiment"""
    es = ExperimentService(current_user)
    exp = es.add(date=form.date.data, scanner=form.scanner.data, field_strength=form.field_strength.data,
                 user=current_user, files=files)
    flash('You successfully created a new experiment.', 'success')
    session['curr_experiment'] = exp.id
    return exp

@blueprint.route('/')
def experiments():
    """List experiments."""
    experiments = Experiment.query.all()
    return render_template('experiments/experiments.html', experiments=experiments)

@blueprint.route('/add', methods=['GET', 'POST'])
def add():
    """Access the add an experiment route and form."""
    form = ExperimentAndScanForm(request.form)
    files = request.files.getlist('scan_file')
    if form.validate_on_submit():
        exp = add_experiment(form, files)

        num2words = {
            1: 'a new scan',
            2: 'two new scans',
            3: 'three new scans'
        }
        try:

            num_scans = len(request.files.getlist('scan_file'))
            flash('You successfully started the process of adding {}.'.format(num2words[num_scans]), 'success')


        except Exception as e:
            flash('There was a problem uploading your scan', 'error')  # todo: error should be color coded red
            global_error_handler(request, e, traceback.format_exc(), cel=False, log_message='generic_message',
                                 user_email=current_user.email, user_message='generic_message', email_user=True,
                                 email_admin=True)



        return redirect(url_for('experiment.single_experiment', id=exp.id))
    else:
        flash_errors(form)
    return render_template('experiments/exp_and_scans.html',form=form)

@blueprint.route('/<id>', methods=['GET'])
def single_experiment(id):
    """Display a single experiment"""
    return render_template('experiments/experiment.html', id=id)

@blueprint.route('/<id>/edit', methods=['GET', 'POST'])
def edit_experiment(id):
    """Access and edit experiment metadata."""
    exp = Experiment.query.filter(Experiment.id==id).first_or_404()
    form = ExperimentForm(obj=exp)

    if form.validate_on_submit():
        form.populate_obj(exp) # update whatever has been changed in the form
        exp.save()
        flash("Experiment metadata updated","success")
        return redirect(url_for('experiment.single_experiment', id=exp.id))
    else:
        flash_errors(form)

    return render_template('experiments/edit_experiment.html',session_form=form, experiment=exp)
