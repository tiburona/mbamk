# -*- coding: utf-8 -*-
""" Displays views. """
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_security import current_user, login_required
from datetime import datetime
from cookiecutter_mbam.utils.error_utils import flash_errors

from cookiecutter_mbam.display.utils import cf_signer, cf_base_url
from cookiecutter_mbam.scan import Scan

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

blueprint = Blueprint('display', __name__, url_prefix='/displays', static_folder='../static')

@blueprint.route('/')
@login_required
def displays():
    """ List all displays available for this user. """
    # For now list and pass the scans that have a aws_orig_key until
    # derivation is updated
    displays = Scan.query.filter(Scan.user_id==current_user.id).all()
    return render_template('displays/displays.html', displays=displays)

@blueprint.route('/experiment/<exp_id>/scan/<scan_id>/slice_view',methods=['GET'])
@login_required
def slice_view(exp_id,scan_id):
    """ Display current user's raw NIFTI file """
    try:
        url = cf_base_url + Scan.query.filter(Scan.user_id==current_user.id). \
                                    filter(Scan.experiment_id==exp_id). \
                                    filter(Scan.id==scan_id).first().orig_aws_key
        signed_url = cf_signer.generate_presigned_url(url, date_less_than=datetime(2020, 12, 12))
        return render_template('displays/slice_view.html',url=signed_url)
    except:
        return render_template('404.html')


@blueprint.route('/test',methods=['GET'])
def test():
    """ Test route to display a NIFTI file in S3 via Cloudfront in papaya """
    url = base_url + 'user/000001/experiment/000001_MR1/scan/T1_1/file/SPGR01_MNI.nii.gz'
    signed_url = cf_signer.generate_presigned_url(url, date_less_than=datetime(2020, 12, 12))

    return render_template('displays/test.html',url=signed_url)
