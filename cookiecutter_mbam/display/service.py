# -*- coding: utf-8 -*-
""" Display service."""
import rsa
from botocore.signers import CloudFrontSigner
from cookiecutter_mbam.base import BaseService
from cookiecutter_mbam.scan import Scan
from cookiecutter_mbam.config import Config as config
from datetime import datetime
from flask import current_app
from flask import url_for

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class DisplayService(BaseService):

    def __init__(self, user):
        # set Cloudfront parameters from config file
        self.cf_base_url = config.CLOUDFRONT_URL
        self.key_id = config.CLOUDFRONT_KEY_ID
        self.private_key = config.CLOUDFRONT_SECRET_KEY
        self.user = user

    def sign_url(self, url):
        """ Return cloudfront signed URL
        :param str url: unsigned Cloudfront url
        :return: signed Cloudfront Url """

        return self._cf_signer().generate_presigned_url(url, date_less_than=datetime(2020, 12, 12))

    def get_nifti_url(self, scan_id):
        """ Get unsigned cloudfront url for a specific scan
        :param int scan_id: id of the scan
        :return: unsigned Cloudfront url """

        aws_key = Scan.get_by_id(scan_id).aws_key
        if aws_key.endswith('.zip'):
            # Case where a .zip was uploaded
            der = [d for d in Scan.get_by_id(scan_id).derivations if (d.process_name == 'dicom_to_nifti') & (d.cloud_storage_key != None)]
            url = self.cf_base_url + der[0].cloud_storage_key
        else:
            # Case where a NIFTI was uploaded
            url = self.cf_base_url + aws_key
        return url

    def get_user_scans(self):
        """ Get all scans belonging to a user that also have orig_aws_key
        :param int user_id:
        :return: list of scan objects """

        return [scan for experiment in self.user.experiments for scan in experiment.scans if scan.aws_key != None]

    def _rsa_signer(self, message):
        """ Create normalized RSA signer to generate a cloudfront signer
        From https://stackoverflow.com/questions/2573919/creating-signed-urls-for-amazon-cloudfront
        :param str message: message to sign
        :return: signed message
        """

        return rsa.sign(message,rsa.PrivateKey.load_pkcs1(self.private_key.encode('utf8')),'SHA-1')

    def _cf_signer(self):
        """ Return cloudfront signer method """

        return CloudFrontSigner(self.key_id, self._rsa_signer)

def displays_url():
    try:
        return url_for('display.displays',_external=True)
    except:
        # Set a default URL for dev in case SERVER_NAME not set
        return 'http://0.0.0.0:8000/displays'
