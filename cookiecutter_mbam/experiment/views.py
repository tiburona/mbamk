# -*- coding: utf-8 -*-
"""Experiment views."""

import traceback
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_security import current_user, login_required
from cookiecutter_mbam.utils.error_utils import flash_errors
from cookiecutter_mbam.utils.model_utils import resource_belongs_to_user
from .forms import ExperimentForm, ExperimentAndScanForm, FlaskForm
from .models import Experiment
from .service import ExperimentService
from cookiecutter_mbam.base.tasks import global_error_handler
from cookiecutter_mbam.config import Config
from cookiecutter_mbam.utils.debug_utils import debug

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


def number_validation(request):
    """Validate that the number of scan files for a given experiment is no more than three"""

    scan_num_error = ''
    num_scans_to_add = len(request.files.getlist('scan_file'))
    if num_scans_to_add > 3:
        scan_num_error = "You can only upload up to three files. Please try again."
    if num_scans_to_add < 1:  # In theory, FileRequired should do this. In practice, it fails to validate when there's
        # a file.
        scan_num_error = "You need to choose a file to upload."
    return scan_num_error


@blueprint.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Access the add an experiment route and form."""

    if not current_user.consented:
        return redirect(url_for('user.consent'))

    if len(current_user.experiments.all()) > Config.EXPERIMENT_CAP - 1:
        return render_template('experiments/too_many_sessions.html')

    form = ExperimentAndScanForm(request.form)

    if form.validate_on_submit():
        error = number_validation(request)
        if error:
            flash(error, 'warning')
            return redirect(url_for('experiment.add'))

        try:
            files = request.files.getlist('scan_file')
            num_scans = len(files)
            add_experiment(form, files)

            flash("You successfully started the process of adding {}. You should receive emails about the upload "
                  "status shortly.".format(num2words[num_scans]), 'success')

        except AssertionError as e:
            error_message = str(e)
            flash(error_message, 'warning')  # todo this should probably be color coded red
            return redirect(url_for('experiment.add'))

        except Exception as e:
            flash("There was a problem uploading your scan", 'error')  # todo: error should be color coded red
            global_error_handler(
                request, e, traceback.format_exc(),
                cel=False, log_message='generic_message', user_email=current_user.email, user_message='generic_message',
                email_user=True, email_admin=True
            )

            flash("You successfully started the process of adding {}. "
                  "You should receive emails about upload status shortly.".format(num2words[num_scans]), 'success')

        return redirect(url_for('public.home'))
    else:
        flash_errors(form)

    return render_template('experiments/experiment_and_scans.html', form=form)


@blueprint.route('/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_experiment(id):
    """Edit experiment metadata."""

    if resource_belongs_to_user(Experiment, id):
        exp = Experiment.get_by_id(id)
        form = ExperimentForm(obj=exp)

        if form.validate_on_submit():
            form.populate_obj(exp)  # update whatever has been changed in the form
            exp.save()

            flash("Session data updated", 'success')

            return redirect(url_for('display.displays'))
        else:
            flash_errors(form)

        return render_template('experiments/edit_experiment.html', session_form=form, experiment=exp)
    else:
        return render_template('403.html')


@blueprint.route('/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete_experiment(id):
    """Delete experiment metadata."""
    if resource_belongs_to_user(Experiment, id):
        exp = Experiment.get_by_id(id)
        form = FlaskForm()

        if form.validate_on_submit():
            for scan in exp.scans:
                # Replace with ScanService.delete() to also delete from XNAT?
                scan.delete()
            exp.delete()

            flash("Deleted the session.", 'success')

            return redirect(url_for('display.displays'))
        else:
            flash_errors(form)

        return render_template('experiments/delete_experiment.html', session_form=form, experiment=exp)
    else:
        return render_template('403.html')
