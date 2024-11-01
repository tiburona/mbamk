from .tasks import *
from cookiecutter_mbam.base import BaseService
from cookiecutter_mbam.utils.debug_utils import debug


config_vars = [
    ('access_key_id', 'CLOUD_STORAGE_ACCESS_KEY_ID'), ('secret_access_key', 'CLOUD_STORAGE_SECRET_ACCESS_KEY'),
    ('bucket_name', 'CLOUD_STORAGE_BUCKET_NAME')
]

class CloudStorageConnection(BaseService):

    def __init__(self):

        self._set_config(config_vars)

        self.auth = {'aws_access_key_id': self.access_key_id,
                     'aws_secret_access_key': self.secret_access_key}
        self.s3_client = boto3.client('s3', **self.auth)
        self.s3_resource = boto3.resource('s3', **self.auth)

    def upload_to_cloud_storage(self, filedir, scan_info, filenames=[], derivation='', delete=True):
        if len(filenames):
            return upload_to_cloud_storage.si(filenames, filedir, self.bucket_name, self.auth, scan_info,
                                              derivation=derivation, delete=delete)
        else:
            return upload_to_cloud_storage.s(filedir, self.bucket_name, self.auth, scan_info, derivation=derivation,
                                             delete=delete)

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

    def delete_folder(self, key):
        bucket = self.s3_resource.Bucket(self.bucket_name)
        for obj in list(bucket.objects.filter(Prefix=key)):
            obj.delete()
