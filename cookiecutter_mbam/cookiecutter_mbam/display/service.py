# -*- coding: utf-8 -*-
""" Display service."""
import rsa
from botocore.signers import CloudFrontSigner
from cookiecutter_mbam.base import BaseService
from cookiecutter_mbam.scan import Scan
from cookiecutter_mbam.config import config_by_name, config_name
from datetime import datetime
from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class DisplayService(BaseService):

    def __init__(self):
        # set Cloudfront parameters from config file
        self.cf_base_url = getattr(config_by_name[config_name], 'AWS')['cloudfront_url']
        self.private_key = getattr(config_by_name[config_name], 'AWS')['cloudfront_private_key']
        self.key_id = getattr(config_by_name[config_name], 'AWS')['cloudfront_key_id']

    def sign_url(self, url):
        """ Return cloudfront signed URL
        :param str url: unsigned Cloudfront url
        :return: signed Cloudfront Url """
        signed_url = self._cf_signer().generate_presigned_url(url, date_less_than=datetime(2020, 12, 12))
        return signed_url

    def return_nifti_url(self, scan_id):
        """ Return unsigned cloudfront url for a specific scan
        :param int scan_id: id of the scan
        :return: unsigned Cloudfront url """
        orig_aws_key = Scan.get_by_id(scan_id).orig_aws_key
        if orig_aws_key.endswith('.zip'):
            # Case where a .zip was uploaded
            der=[d for d in Scan.get_by_id(scan_id).derivations if (d.process_name == 'dicom_to_nifti') & (d.cloud_storage_key != None)]
            url = self.cf_base_url + der[0].cloud_storage_key
        else:
            # Case where a NIFTI was uploaded
            url = self.cf_base_url + orig_aws_key
        return url

    def return_user_scans(self, user_id):
        """ Return all scans belonging to a user that also have orig_aws_key
        :param int user_id:
        :return: list of scan objects """
        scans = Scan.query.filter(Scan.user_id==user_id).filter(Scan.orig_aws_key != None).all()
        # OR SOMETHING LIKE scans = [scan for scan in experiment for experiment in current_user.experiments if scan.orig_aws_key != None]
        return scans

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
