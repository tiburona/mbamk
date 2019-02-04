import boto3

class CloudStorageConnection:

    def __init__(self, config):

        self.s3_config = config

        self.s3 = boto3.client(
            's3',
            aws_access_key_id=config['access_key_id'],
            aws_secret_access_key=config['secret_access_key']
        )
        self.bucket = 'mbam-test'

    def upload_scan(self, user_id, experiment_id, scan_id, file_path, filename):
        key = 'user/{}/experiment/{}/scan/{}/file/{}'.format(user_id, experiment_id, scan_id, filename)
        self.s3.put_object(Bucket=self.bucket, Key=key)
        result = self.s3.upload_file(file_path, self.bucket, key)
        return (key, result)
