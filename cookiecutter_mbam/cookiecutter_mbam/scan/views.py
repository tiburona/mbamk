# -*- coding: utf-8 -*-
"""Scan views."""
import traceback

from flask import Blueprint, flash, redirect, url_for, render_template
from flask_security import current_user
from .models import Scan
from .forms import EditScanForm
from cookiecutter_mbam.utils.error_utils import flash_errors

from cookiecutter_mbam.base.tasks import global_error_handler
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
        global_error_handler(request, e, traceback.format_exc(), cel=False, log_message='generic_message',
                             user_email=current_user.email, user_message='generic_message', email_user=True,
                             email_admin=True)

    return redirect(url_for('experiment.experiments'))


@blueprint.route('/<id>/edit', methods=['GET', 'POST'])
def edit_scan(id):
    """Access and edit scan metadata (label)."""
    scan = Scan.query.filter(Scan.id==id).first_or_404()
    form = EditScanForm(obj=scan)

    if form.validate_on_submit():
        form.populate_obj(scan) # update whatever has been changed in the form
        scan.save()
        flash('Scan metadata updated','success')
        return redirect(url_for('display.displays'))
    else:
        flash_errors(form)

    return render_template('scans/edit_scan.html',session_form=form, scan=scan)
