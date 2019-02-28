import requests
import time
import json
import os
from celery.contrib import rdb
# from cookiecutter_mbam.app import make_celery
# celery = make_celery()

from cookiecutter_mbam import celery

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s


@celery.task
def celery_upload(server, user, password, url, file_path):
    files = {'file': ('T1.nii.gz', open(file_path, 'rb'), 'application/octet-stream')}
    with init_session(user, password) as s:
        r = s.put(server + url, files=files)
        return r

@celery.task
def celery_import(server, user, password, file_path, url):
    files = {'file': ('DICOMS.zip', open(file_path, 'rb'), 'application/octet-stream')}
    with init_session(user, password) as s:
        r = s.post(server + '/data/services/import', files=files, data={'dest': url, 'overwrite':'delete'})
        # return r # the error is here

@celery.task(time_limit=10000)
def poll_cs(xnat_credentials, container_id):
    server, user, password = xnat_credentials
    with init_session(user, password) as s:
        while True:
            r = s.get(server + '/xapi/containers/{}'.format(container_id))
            status = json.loads(r.text)['status']
            if status in ['Complete', 'Failed', 'Killed', 'Killed (Out of Memory)']:
                return status
            time.sleep(5)

@celery.task
def dl_file_from_xnat(container_status, xnat_credentials, url, file_path):
    server, user, password = xnat_credentials
    if container_status == 'Complete':
        with init_session(user, password) as s:
            r = s.get(url)
            if r.ok:
                result = json.loads(r.text)['ResultSet']['Result'][0]
                response = s.get(server + result['URI'])
                if response.ok:
                    with open(os.path.join(file_path, result['Name']), 'wb') as f:
                        f.write(response.content)
                        return result['Name']

        return r # need some kind of method here that communicates that the process completed but the file is not accessible
    else:
        pass
        # should probably break chain before this.
