import boto3
from cookiecutter_mbam.utility.celery_utils import get_celery_worker_status
from .tasks import *
from flask import current_app
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

    def _get_celery_status(self):
        """Verify Celery worker is registered
        Sets default to upload synchronously, but if celery worker is registered, changes default.
        """
        self.celery_upload = False
        celery_status = get_celery_worker_status(celery)
        registered_tasks = celery_status['registered_tasks']
        if registered_tasks:
            for key in registered_tasks:
                for task in registered_tasks[key]:
                    if 'upload_scan_to_cloud_storage' in task:
                        self.celery_upload = True

    def upload_chain(self, filename, filedir, scan_info):
        return upload_scan_to_cloud_storage.s(filename, filedir, self.bucket_name, self.auth, scan_info)

    def upload_scan(self, filename, dir, scan_info):
        """ Upload a scan to AWS

        Checks whether upload task is registered with a Celery worker.  If so, calls Celery upload.  If not, uploads the
        file to AWS directly.

        :param str filename: the name of the file
        :param str dir: the directory where the file is located
        :param tuple scan_info: a 3-tuple of strings with the XNAT subject, experiment, and scan identifiers
        """

        if self.celery_upload:
            upload_scan_to_cloud_storage(filename, self.bucket_name, dir, self.auth, scan_info)
        else:
            key = self._construct_key(scan_info, filename)
            file_path = os.path.join(dir, filename)
            self.s3_client.put_object(Bucket=self.bucket_name, Key=key)
            self.s3_client.upload_file(file_path, self.bucket_name, key)

    def _construct_key(self, scan_info, filename):
        """
        :param tuple scan_info: a 3-tuple of strings with the XNAT subject, experiment, and scan identifiers
        :param str filename: the name of the file
        :return str: key
        """
        user_id, experiment_id, scan_id = scan_info
        return 'user/{}/experiment/{}/scan/{}/file/{}'.format(user_id, experiment_id, scan_id, filename)


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


