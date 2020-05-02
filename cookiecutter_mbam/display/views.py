# -*- coding: utf-8 -*-
""" Displays views. """
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_security import current_user, login_required
from cookiecutter_mbam.utils.error_utils import flash_errors
from cookiecutter_mbam.utils.model_utils import resource_belongs_to_user
from cookiecutter_mbam.scan.models import Scan
from .service import DisplayService
from cookiecutter_mbam.experiment.forms import ExperimentForm
from cookiecutter_mbam.scan.forms import EditScanForm

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

blueprint = Blueprint('display', __name__, url_prefix='/displays', static_folder='../static')

@blueprint.route('/')
@login_required
def displays():
    """ List all displays available for this user. """
    # For now list and pass the scans that have a aws_orig_key until
    # derivation is updated
    session_form=ExperimentForm()
    scan_form=EditScanForm()

    dis = DisplayService(user=current_user).get_user_scans()
    print(dis)

    return render_template('displays/displays.html', displays=dis, session_form=session_form, scan_form=scan_form)

@blueprint.route('/scan/<id>/slice_view',methods=['GET'])
@login_required
def slice_view(id):
    """ Display current user's raw NIFTI file """
    if resource_belongs_to_user(Scan, id):
        try:
            ds = DisplayService(user=current_user)
            url = ds.get_nifti_url(id)
            signed_url = ds.sign_url(url)
            scan=Scan.get_by_id(id)
            return render_template('displays/slice_view.html', url=signed_url, scan=scan, scan_form=EditScanForm())
        except:
            # TODO: Log this error
            return render_template('404.html')
    else:
        return render_template('403.html')


@blueprint.route('/mikes_view',methods=['GET'])
def mikes_view():
    """ Display Mike's 3D brain """
    return render_template('displays/threed_view.html')


@blueprint.route('/brain_explorer.html')
def brain_explorer():
    return render_template('displays/brain_explorer.html')

@blueprint.route('/test',methods=['GET'])
def test():
    """ Test route to display a NIFTI file in S3 via Cloudfront signed URL in papaya """
    url = DisplayService(user=current_user).cf_base_url + 'test/MNI_SPGR01.nii.gz'
    signed_url = DisplayService(user=current_user).sign_url(url)

    return render_template('displays/test.html',url=signed_url)
