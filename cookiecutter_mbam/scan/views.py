# -*- coding: utf-8 -*-
"""Scan views."""
import traceback

from flask import Blueprint, flash, redirect, url_for, render_template, request
from flask_security import current_user, login_required
from .models import Scan
from cookiecutter_mbam.experiment.models import Experiment
from .forms import EditScanForm, DeleteScanForm
from cookiecutter_mbam.utils.error_utils import flash_errors
from cookiecutter_mbam.utils.model_utils import resource_belongs_to_user
from cookiecutter_mbam.base.tasks import global_error_handler
from .service import ScanService
from cookiecutter_mbam.utils.debug_utils import debug

blueprint = Blueprint('scan', __name__, url_prefix='/scans', static_folder='../static')

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
@login_required
def edit_scan(id):
    """Access and edit scan metadata (label)."""
    if resource_belongs_to_user(Scan, id):
        next=request.args.get('next') # query param to determine where to redirect the user after editing
        scan = Scan.query.filter(Scan.id==id).first_or_404()
        form = EditScanForm(obj=scan)

        if form.validate_on_submit():
            form.populate_obj(scan) # update whatever has been changed in the form
            scan.save()
            flash('Scan label updated','success')
            if next == 'slice_view':
                return redirect(url_for('display.slice_view',id=id))
            else:
                return redirect(url_for('display.displays'))
        else:
            flash_errors(form)

        return render_template('scans/edit_scan.html',scan_form=form, scan=scan)
    else:
        return render_template('403.html')

@blueprint.route('/<id>/delete', methods=['GET','POST'])
@login_required
def delete_scan(id):
    """ Delete the scan."""
    if resource_belongs_to_user(Scan, id):
        scan = Scan.query.filter(Scan.id==id).first_or_404()
        exp = scan.experiment
        form = DeleteScanForm(obj=scan)
        ss=ScanService(current_user,exp)

        if form.validate_on_submit():
            form.populate_obj(scan)

            ss.delete(scan.id, delete_from_xnat=True, delete_from_S3=True)

            if len(exp.scans.all()) == 0:
                exp.delete()

            flash('Scan removed.','success')
            return redirect(url_for('display.displays'))
        else:
            flash_errors(form)

        return render_template('scans/delete_scan.html',scan_form=form, scan=scan)
    else:
        return render_template('403.html')
