
import boto3
import os
import shutil

from cookiecutter_mbam import celery


@celery.task
def upload_to_cloud_storage(filenames, filedir, bucket_name, auth, scan_info, derivation='', delete=True):
    user_id, experiment_id, scan_id = scan_info

    if not isinstance(filenames, list):
        filenames = [filenames]

    for filename in filenames:
        key_path = 'user/{}/experiment/{}/scan/{}'.format(user_id, experiment_id, scan_id)
        if len(derivation):
            key_path += '/derivation/{}'.format(derivation)
        key = key_path +  '/file/{}'.format(filename)
        file_path = os.path.join(filedir, filename)
        s3_client = boto3.client('s3', **auth)
        s3_client.upload_file(file_path, bucket_name, key)
    if delete:
        shutil.rmtree(filedir,ignore_errors=True)
    if len(filenames) > 1:
        return key_path
    else:
        return key
