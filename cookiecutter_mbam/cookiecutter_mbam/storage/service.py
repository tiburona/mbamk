from cookiecutter_mbam.utils.celery_utils import get_celery_worker_status
from .tasks import *
from flask import current_app
from flask import current_app

from cookiecutter_mbam.utils.celery_utils import get_celery_worker_status
from .tasks import *


def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class CloudStorageConnection:

    def __init__(self, config):

        self.auth = {'aws_access_key_id': config['access_key_id'],
                     'aws_secret_access_key': config['secret_access_key']}
        self.s3_client = boto3.client('s3', **self.auth)
        self.s3_resource = boto3.resource('s3', **self.auth)
        self.bucket_name = config['bucket_name']
        self._get_celery_status()

    def _construct_key(self, scan_info, filename):
        """
        :param tuple scan_info: a 3-tuple of strings with the XNAT subject, experiment, and scan identifiers
        :param str filename: the name of the file
        :return str: key
        """
        user_id, experiment_id, scan_id = scan_info
        return 'user/{}/experiment/{}/scan/{}/file/{}'.format(user_id, experiment_id, scan_id, filename)

    def upload_to_cloud_storage(self, filename, filedir, scan_info):
        return upload_scan_to_cloud_storage.si(filename, filedir, self.bucket_name, self.auth, scan_info)

    def object_exists(self, key):
        """
        :param key:
        :return:
        """
        bucket = self.s3_resource.Bucket(self.bucket_name)
        objs = list(bucket.objects.filter(Prefix=key))
        if len(objs) > 0 and objs[0].key == key:
            return objs[0]
        else:
            return False

    def object_of_min_size_exists(self, key, min_size):
        return self.object_exists(key) and self.object_exists(key).size > min_size

    def delete_object(self, key):
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)


