# -*- coding: utf-8 -*-
"""Overlays views."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_security import current_user
import boto3, os, rsa
from datetime import datetime
from cookiecutter_mbam.utils.error_utils import flash_errors

#from .service import ExperimentService

blueprint = Blueprint('overlay', __name__, url_prefix='/overlays', static_folder='../static')

# @blueprint.route('/')
# def overlays():
#     """List overlays available for this user."""
#     # list all overlays available for the user
#     overlays = current_user.
#     # pass overlays to overlays.html template
#     return render_template('overlays/overlays.html', overlays=overlays)
#
# @blueprint.route('/<id>/slice_view', methods=['GET'])
# def slice_view(id):
#     """ Display the overlay in 2d using papaya viewer."""
#     # Grab the scan or derivation
#     # overlay = scan.derivate.query(id=id).first_or_404
#
#     # Access xnat_uri or cloud_storage_key to pass to papaya viewer
#     overlay.cloud_storage_key
#     return render_template('overlays/slice_view.html',overlay=overlay)

@blueprint.route('/test',methods=['GET'])
def test():
    """ See if you can use this route to display a NIFTI file in S3 in papaya! """
    #url = "https://mbam-test-sp.s3.amazonaws.com/user/000001/experiment/000001_MR1/scan/T1_1/file/SPGR01_MNI.nii.gz"
    url = "https://dc2khv0msnx9b.cloudfront.net/user/000001/experiment/000001_MR1/scan/T1_1/file/SPGR01_MNI.nii.gz"
    key_id='APKAJZ3J6OMQJKG2PO4Q'

    from botocore.signers import CloudFrontSigner
    # First you create a cloudfront signer based on a normalized RSA signer::
    import rsa

    def rsa_signer(message):
        private_key = open('pk-APKAJZ3J6OMQJKG2PO4Q.pem', 'r').read()
        return rsa.sign(
            message,
            rsa.PrivateKey.load_pkcs1(private_key.encode('utf8')),
            'SHA-1')  # CloudFront requires SHA-1 hash

    cf_signer = CloudFrontSigner(key_id, rsa_signer)

    # To sign with a canned policy::
    signed_url = cf_signer.generate_presigned_url(
        url, date_less_than=datetime(2020, 12, 12))

    # To sign with a custom policy::
    #signed_url = cf_signer.generate_presigned_url(url)

    print(os.getcwd())
    return render_template('overlays/test.html',url=signed_url)
