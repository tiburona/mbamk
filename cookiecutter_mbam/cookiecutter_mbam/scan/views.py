# -*- coding: utf-8 -*-
"""Scan views."""
from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from flask_login import current_user
from .forms import ScanForm, ExperimentAndScanForm
from .service import ScanService
from cookiecutter_mbam.experiment.views import add_experiment
from cookiecutter_mbam.utils import flash_errors

blueprint = Blueprint('scan', __name__, url_prefix='/scans', static_folder='../static')

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


def validate_number_of_files(request, failure_redirect):
    """Ensure number of files uploaded is between 1 and 3, inclusive"""
    if len(request.files.getlist('scan_file')) > 3:
        flash('You can upload up to three files.', 'warning')
        return redirect(url_for(failure_redirect))
    if len(request.files.getlist('scan_file')) < 1:
        # This is a workaround for FileRequired() failing inexplicably.  Long-term should fix this.
        flash('A file is required.', 'warning')
        return redirect(url_for(failure_redirect))

def add_scan(request, exp_id):
    """Add a scan"""
    user_id = str(current_user.get_id())
    for f in request.files.getlist('scan_file'):
        ScanService(user_id, exp_id).add(f)
    flash('You successfully added a new scan.', 'success')
    return redirect(url_for('experiment.experiments'))

@blueprint.route('/add', methods=['GET', 'POST'])
def add():
    """Access the add scan route and form."""
    form = ScanForm()
    if form.validate_on_submit():
        wrong_number_of_files = validate_number_of_files(request, 'scan.add_experiment_and_scans')
        if wrong_number_of_files:
            return wrong_number_of_files
        exp_id = str(session['curr_experiment'])
        return add_scan(request, exp_id)
    else:
        flash_errors(form)
    return render_template('scans/upload.html',scan_form=form)

@blueprint.route('/add_experiment_and_scans', methods=['GET', 'POST'])
def add_experiment_and_scans():
    """Acess the add_experiment_and_scans route and form"""
    form = ExperimentAndScanForm(request.form)
    if form.validate_on_submit():
        wrong_number_of_files = validate_number_of_files(request, 'scan.add_experiment_and_scans')
        if wrong_number_of_files:
            return wrong_number_of_files
        exp_id = add_experiment(form)
        return add_scan(request, exp_id)
    else:
        flash_errors(form)
    return render_template('scans/experiment_and_scans.html', experiment_and_scan_form=form)