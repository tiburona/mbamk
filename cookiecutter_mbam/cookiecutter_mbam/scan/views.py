# -*- coding: utf-8 -*-
"""Scan views."""
from flask import Blueprint, render_template, flash, redirect, url_for, session
from flask_login import current_user
from .forms import ScanForm
from .service import ScanService
from cookiecutter_mbam.utils import flash_errors

blueprint = Blueprint('scan', __name__, url_prefix='/scans', static_folder='../static')

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


@blueprint.route('/add', methods=['GET', 'POST'])
def add():
    """Add a scan."""
    form = ScanForm()
    if form.validate_on_submit():
        f = form.scan_file.data
        user_id = str(current_user.get_id())
        exp_id = str(session['curr_experiment'])
        ScanService(user_id, exp_id).upload(f)
        flash('You successfully added a new scan.', 'success')
        return redirect(url_for('experiment.experiments'))
    else:
        flash_errors(form)
    return render_template('scans/upload.html',scan_form=form)