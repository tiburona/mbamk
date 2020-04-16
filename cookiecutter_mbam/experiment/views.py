# -*- coding: utf-8 -*-
"""Experiment views."""

import traceback
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_security import current_user, login_required
from cookiecutter_mbam.utils.error_utils import flash_errors
from .forms import ExperimentForm, ExperimentAndScanForm, FlaskForm
from .models import Experiment
from .service import ExperimentService
from cookiecutter_mbam.scan.service import ScanService
from cookiecutter_mbam.base.tasks import global_error_handler


from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


blueprint = Blueprint('experiment', __name__, url_prefix='/experiments', static_folder='../static')

num2words = {
        1: 'one scan',
        2: 'two scans',
        3: 'three scans'
    }

def add_experiment(form, files):
    """Add an experiment"""
    es = ExperimentService(current_user)
    es.add(date=form.date.data, scanner=form.scanner.data, field_strength=form.field_strength.data,
                 user=current_user, files=files)

@blueprint.route('/')
def experiments():
    """List experiments."""
    # todo: this makes no sense, please eventually change.
    experiments = Experiment.query.all()
    return render_template('experiments/experiments.html', experiments=experiments)

def scan_number_validation(request):
    """Validate that the number of scan files for a given experiment is at least one and no more than three"""

    num_scans_to_add = len(request.files.getlist('scan_file'))
    if num_scans_to_add < 1:
        # This is a workaround for FileRequired() failing inexplicably.  Long-term should fix this.
        return 'A file is required.'
    if num_scans_to_add > 3:
            return 'You can upload up to three files.'
    else:
        return ''


@blueprint.route('/dev_add', methods=['GET', 'POST'])
@login_required
def dev_add():
    form = ExperimentAndScanForm(request.form)
    if form.validate_on_submit():
        files = request.files.getlist('scan_file')
        add_experiment(form, files)
        num_scans = len(files)
        flash('You successfully started the process of adding {}.'.format(num2words[num_scans]), 'success')
        return redirect(url_for('experiment.experiments'))
    return render_template('experiments/exp_and_scans.html', form=form)


@login_required
@blueprint.route('/add', methods=['GET', 'POST'])
def add():
    """Access the add an experiment route and form."""

    if not current_user.consented:
        return redirect(url_for('user.consent'))

    form = ExperimentAndScanForm(request.form)

    if form.validate_on_submit():
        scan_number_error = scan_number_validation(request)
        if len(scan_number_error):
            flash(scan_number_error, 'warning')
            return redirect(url_for('experiment.add'))

        try:
            files = request.files.getlist('scan_file')
            add_experiment(form, files)
            num_scans = len(files)

            flash('You successfully started the process of adding {}.'.format(num2words[num_scans]), 'success')

        except Exception as e:
            flash('There was a problem uploading your scan', 'error')  # todo: error should be color coded red
            global_error_handler(request, e, traceback.format_exc(), cel=False, log_message='generic_message',
                                 user_email=current_user.email, user_message='generic_message', email_user=True,
                                 email_admin=True)

        return redirect(url_for('experiment.experiments'))
    else:
        flash_errors(form)
    return render_template('experiments/experiment_and_scans.html',form=form)

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
        flash('Experiment metadata updated','success')
        return redirect(url_for('display.displays'))
    else:
        flash_errors(form)

    return render_template('experiments/edit_experiment.html',session_form=form, experiment=exp)

@blueprint.route('/<id>/delete', methods=['GET', 'POST'])
def delete_experiment(id):
    """Access and edit experiment metadata."""
    exp = Experiment.query.filter(Experiment.id==id).first_or_404()
    form = FlaskForm()

    if form.validate_on_submit():
        exp.delete()
        # for scan in exp.scans:
        #     scan.delete()
        flash('Deleted the session.','success')
        return redirect(url_for('display.displays'))
    else:
        flash_errors(form)

    return render_template('experiments/delete_experiment.html', session_form=form, experiment=exp)
