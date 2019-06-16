import time
import os
from cookiecutter_mbam import celery
from cookiecutter_mbam.utils.request_utils import init_session
from .utils import crop


@celery.task
def create_resources(xnat_credentials, ids, levels, import_service, archive_prefix):
    """
    :param tuple xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param dict ids:
    :param list levels:
    :param bool import_service:
    :param archive_prefix:
    :return:
    """
    server, user, password = xnat_credentials
    xnat_ids, existing_xnat_ids = ids
    uri = archive_prefix  # todo: decide whether to use prearchive
    uris = {}

    if import_service:
        levels = levels[:-3]

    with init_session(user, password) as s:
        for level in levels:

            exists_already = level in ['subject', 'experiment'] and len(existing_xnat_ids[level]['xnat_id'])
            d = existing_xnat_ids if exists_already else xnat_ids

            uri = os.path.join(uri, level + 's', d[level]['xnat_id'])
            uris[level] = uri

            try:
                query = xnat_ids[level]['query_string']
            except:  # todo specify KeyError here?
                query = ''

            if not exists_already:
                r = s.put(url=server+ uri + query)
        return uris

@celery.task
def upload_scan_to_xnat(uris, xnat_credentials, file_path):
    url = uris['file']
    server, user, password = xnat_credentials
    files = {'file': ('T1.nii.gz', open(file_path, 'rb'), 'application/octet-stream')}
    with init_session(user, password) as s:
        s.put(server + url, files=files)
    return uris

@celery.task
def import_scan_to_xnat(uris, xnat_credentials, file_path):
    server, user, password = xnat_credentials
    url = uris['experiment']
    files = {'file': ('DICOMS.zip', open(file_path, 'rb'), 'application/octet-stream')}
    with init_session(user, password) as s:
        r = s.post(server + '/data/services/import', files=files, data={'dest': url, 'overwrite':'delete'})
        # todo: if response has good info about whether the file uploaded, should use that
        # to send a message back to user about success of upload.
    return uris

@celery.task
def get_latest_scan_info(uris, xnat_credentials):
    server, user, password = xnat_credentials
    with init_session(user, password) as s:
        scans = s.get(server + uris['experiment'] + '/scans').json()['ResultSet']['Result']
        scans = sorted(scans, key=lambda scan: int(scan['xnat_imagescandata_id']))
        scan_uri = scans[-1]['URI']
        scan_id = scans[-1]['ID']
        return {'xnat_id': scan_id, 'xnat_uri': scan_uri}

# todo: figure out how to specify action to take if celery times out.
@celery.task(time_limit=10000)
def poll_cs(container_id, xnat_credentials):
    server, user, password = xnat_credentials
    with init_session(user, password) as s:
        while True:
            r = s.get(server + '/xapi/containers/{}'.format(container_id))
            status = r.json()['status']
            if status in ['Complete', 'Failed', 'Killed', 'Killed (Out of Memory)']:
                return status
            time.sleep(5)
    return 'none'

@celery.task
def dl_file_from_xnat(scan_uri, xnat_credentials, file_path):
    server, user, password = xnat_credentials
    with init_session(user, password) as s:
        r = s.get(server + os.path.join(scan_uri, 'resources', 'NIFTI', 'files'))
        if r.ok:
            print("I shouldn't get here")
            result = r.json()['ResultSet']['Result'][0]
            response = s.get(server + result['URI'])
            if response.ok:
                with open(os.path.join(file_path, result['Name']), 'wb') as f:
                    f.write(response.content)
                    return result['Name']
            else:
                raise ValueError(f'Unexpected status code: {response.status_code}')
        else:
            raise ValueError(f'Unexpected status code: {response.status_code}')
    return r


@celery.task
def launch_command(uri, xnat_credentials, project, command_ids):
    data = {'scan': crop(uri, '/experiments')}
    server, user, password = xnat_credentials
    command_id, wrapper_id = command_ids
    url = '/xapi/projects/{}/commands/{}/wrappers/{}/launch'.format(project, command_id, wrapper_id)
    with init_session(user, password) as s:
        r = s.post(server + url, data)
        return r.json()['container-id']
