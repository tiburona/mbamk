# -*- coding: utf-8 -*-
""" Utility methods for display views. """
import rsa
from botocore.signers import CloudFrontSigner
from cookiecutter_mbam.config import config_by_name, config_name

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
cf_base_url = getattr(config_by_name[config_name], 'AWS')['cloudfront_url']
