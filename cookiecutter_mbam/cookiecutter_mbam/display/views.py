# -*- coding: utf-8 -*-
"""Overlays views."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_security import current_user
import boto3, os, rsa
from datetime import datetime
from cookiecutter_mbam.utils.error_utils import flash_errors
from cookiecutter_mbam.config import config_by_name, config_name

from botocore.signers import CloudFrontSigner


blueprint = Blueprint('display', __name__, url_prefix='/displays', static_folder='../static')

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

def rsa_signer(message):
    """ Create normalized RSA signer to generate a cloudfront signer
    From https://stackoverflow.com/questions/2573919/creating-signed-urls-for-amazon-cloudfront

    :param str message: message to sign
    :return: signed message
    """
    private_key = getattr(config_by_name[config_name], 'AWS')['cloudfront_private_key']
    return rsa.sign(message,rsa.PrivateKey.load_pkcs1(private_key.encode('utf8')),'SHA-1')


key_id = getattr(config_by_name[config_name], 'AWS')['cloudfront_key_id']
cf_signer = CloudFrontSigner(key_id, rsa_signer)

@blueprint.route('/test',methods=['GET'])
def test():
    """ See if you can use this route to display a NIFTI file in S3 in papaya! """

    # https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-task-list.html
    #url = "https://mbam-test-sp.s3.amazonaws.com/user/000001/experiment/000001_MR1/scan/T1_1/file/SPGR01_MNI.nii.gz"
    base_url = getattr(config_by_name[config_name], 'AWS')['cloudfront_url']
    url = base_url + 'user/000001/experiment/000001_MR1/scan/T1_1/file/SPGR01_MNI.nii.gz'


    # To sign with a canned policy::
    signed_url = cf_signer.generate_presigned_url(
        url, date_less_than=datetime(2020, 12, 12))

    # To sign with a custom policy::
    #signed_url = cf_signer.generate_presigned_url(url)

    return render_template('displays/test.html',url=signed_url)
