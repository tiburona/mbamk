# -*- coding: utf-8 -*-
"""Scan views."""
import traceback

from flask import Blueprint, render_template, flash, redirect, url_for, session
from flask import request
from flask_security import current_user, login_required

from cookiecutter_mbam.experiment import Experiment
from cookiecutter_mbam.experiment.views import add_experiment
from cookiecutter_mbam.base.tasks import global_error_handler
from cookiecutter_mbam.utils.error_utils import flash_errors
from .forms import ScanForm, ExperimentAndScanForm
from .service import ScanService

blueprint = Blueprint('scan', __name__, url_prefix='/scans', static_folder='../static')

from flask import current_app


def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


def add_scans(request, exp_id):
    """Add scan files"""
    num2words = {
        1: 'a new scan',
        2: 'two new scans',
        3: 'three new scans'
    }
    user_id = str(current_user.get_id())
    try:
        for f in request.files.getlist('scan_file'):
            ScanService(user_id, exp_id).add(f)

        num_scans = len(request.files.getlist('scan_file'))
        flash('You successfully started the process of adding {}.'.format(num2words[num_scans]), 'success')

    except Exception as e:
        flash('There was a problem uploading your scan', 'error')  # todo: error should be color coded red
        global_error_handler(request, e, traceback.format_exc(), log_message='generic_message',
                             user_email=current_user.email, user_message='generic_message', email_user=True,
                             email_admin=False)

    return redirect(url_for('experiment.experiments'))


def scan_number_validation(request, add_exp):
    """Validate that the number of scan files for a given experiment is at least one and no more than three"""
    num2words = {
        1: 'one scan',
        2: 'two scans',
        3: 'three scans'
    }
    num_scans_to_add = len(request.files.getlist('scan_file'))
    if num_scans_to_add < 1:
        # This is a workaround for FileRequired() failing inexplicably.  Long-term should fix this.
        return 'A file is required.'
    if add_exp:
        if num_scans_to_add > 3:
            return 'You can upload up to three files.'
    else:
        num_scans = Experiment.get_by_id(str(session['curr_experiment'])).num_scans
        if num_scans + num_scans_to_add > 3:
            return "A session can only have three scans.  You already have {}.".format(num2words[num_scans])
    return ''


def meta_add(form, request, redirect_route, template, add_exp=False):
    """Validate form, initiate adding experiments and/or scans, display messages to user and redirect"""
    if form.validate_on_submit():
        scan_number_error = scan_number_validation(request, add_exp)
        if len(scan_number_error):
            flash(scan_number_error, 'warning')
            return redirect(url_for(redirect_route))
        if add_exp:
            exp_id = add_experiment(form)
        else:
            exp_id = str(session['curr_experiment'])
        return add_scans(request, exp_id)
    else:
        flash_errors(form)
    return render_template(template, form=form)


@blueprint.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Access the add scan route and form."""
    return meta_add(ScanForm(request.form), request, 'scan.add', 'scans/upload.html')


@blueprint.route('/add_experiment_and_scans', methods=['GET', 'POST'])
@login_required
def add_experiment_and_scans():
    """Access the add_experiment_and_scans route and form"""
    if not current_user.consented:
        return redirect(url_for('user.profile'))

    return meta_add(ExperimentAndScanForm(request.form), request, 'scan.add_experiment_and_scans',
                    'scans/experiment_and_scans.html', add_exp=True)
