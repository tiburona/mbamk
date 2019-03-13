
import boto3
import os

from cookiecutter_mbam import celery

@celery.task
def upload_scan(filename, bucket_name, dir, auth, scan_info):
    user_id, experiment_id, scan_id = scan_info
    file_path = os.path.join(dir, filename)
    key = 'user/{}/experiment/{}/scan/{}/file/{}'.format(user_id, experiment_id, scan_id, filename)
    s3_client = boto3.client('s3', **auth)
    s3_client.upload_file(file_path, bucket_name, key)
    # delete local file to clean up?
    return key