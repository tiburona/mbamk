import boto3

class CloudStorageConnection:

    def __init__(self, config):

        self.auth = {'aws_access_key_id': config['access_key_id'],
                     'aws_secret_access_key': config['secret_access_key']}
        self.s3_client = boto3.client('s3', **self.auth)
        self.s3_resource = boto3.resource('s3', **self.auth)
        self.bucket_name = config['bucket_name']

    # Note about this method: duplicates functionality in tasks.py.  Do we want to keep non-celery method?
    # If so.
    def upload_scan(self, scan_info, file, filename, file_obj=False):
        """ Upload a scan to AWS
        :param scan_info: a 3-tuple with the MBAM database user id, experiment id, and scan id
        :param file: if file_obj is false, the full path
        :param filename:
        :param file_obj:
        :return:
        """
        user_id, experiment_id, scan_id = scan_info
        key = 'user/{}/experiment/{}/scan/{}/file/{}'.format(user_id, experiment_id, scan_id, filename)
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key)
        if file_obj:
            self.s3_client.upload_fileobj(file, self.bucket_name, key)
        else:
            self.s3_client.upload_file(file, self.bucket_name, key)
        return key

    def object_exists(self, key):
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


