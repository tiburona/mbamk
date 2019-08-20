import time
import os
from celery.exceptions import SoftTimeLimitExceeded
from cookiecutter_mbam import celery
from cookiecutter_mbam.utils.request_utils import init_session
from .utils import crop
from cookiecutter_mbam.mbam_logging import celery_logger

from cookiecutter_mbam.mbam_logging import app_logger

app_logger.error("Celery backend in tasks {}".format(celery.backend), extra={'email_admin': False} )



@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def upload_scan_to_xnat(self, xnat_credentials, file_path, experiment_uri, request_url):
    """ Upload a NIFTI format scan to XNAT

    :param self: the task object
    :param dict uris: a dictionary with levels as keys that contains the path for the file to upload (as well as the
    uris for subject, experiment, etc.)
    :param tuple xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param str file_path: the location of the file on the local disk
    :return: uris
    """

    server, user, password = xnat_credentials
    files = {'file': ('T1.nii.gz', open(file_path, 'rb'), 'application/octet-stream')}
    with init_session(user, password) as s:
        r = s.put(request_url, files=files)
        if r.ok:
            return experiment_uri
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: /n {r.text}')

# note:
@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def import_scan_to_xnat(self, xnat_credentials, file_path, experiment_uri, request_url):
    """Import a DICOM format scan to XNAT

    :param self: the task object
    :param dict uris: a dictionary with levels as keys that contains the experiment uri, the import destination
    :param tuple xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param str file_path: the location of the file on the local disk
    :return: uris

    This is the task invoked when the scan is in DICOM format.
    """
    server, user, password = xnat_credentials
    files = {'file': ('DICOMS.zip', open(file_path, 'rb'), 'application/octet-stream')}
    with init_session(user, password) as s:
        r = s.put(request_url)
        r = s.post(server + '/data/services/import', files=files, data={'dest': experiment_uri, 'overwrite':'delete'})
        if r.ok:
            return experiment_uri
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: /n {r.text}')

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def get_latest_scan_info(self, experiment_uri, xnat_credentials):
    """ Get XNAT uri and id of the last uploaded scan for the current experiment

     XNAT automatically sets the ID of an imported scan and MBAM makes no attempt to overwrite it.  This function
     retrieves that information (regardless of whether the scan was uploaded or imported.)

    :param self: the task object
    :param dict uris: a dictionary with levels as keys that contains the experiment uri
    :param tuple xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :return: a dictionary of the XNAT id and XNAT uri of the scan
    :rtype: dict
    """
    server, user, password = xnat_credentials
    with init_session(user, password) as s:
        r = s.get(server + experiment_uri + '/scans')
        if r.ok:
            scans = r.json()['ResultSet']['Result']
            scans = sorted(scans, key=lambda scan: int(scan['xnat_imagescandata_id']))
            scan_uri = scans[-1]['URI']
            scan_id = scans[-1]['ID']
            return {'xnat_id': scan_id, 'xnat_uri': scan_uri}
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: /n {r.text}')

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def gen_dicom_conversion_data(self, uri):
    """ Generate the payload for the post request that launches the DICOM converstion command

    :param self: the task object
    :param str uri: the uri of a scan
    :return: a dictionary with the payload to be included with the post request to launch dicom conversion
    """

    return {'scan': crop(uri, '/experiments')}

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def launch_command(self, data, xnat_credentials, project, command_ids):
    """ Launch a command in XNAT

    :param self: the task object
    :param dict data: a dictionary with the payload to be included with the post request to launch the command
    :param tuple xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param str project: the XNAT project
    :param tuple command_ids: a two-tuple of the id of the command and the id of the wrapper in the XNAT host executing
    the command
    :return: container id
    :rtype: str
    """
    server, user, password = xnat_credentials
    command_id, wrapper_id = command_ids
    url = '/xapi/projects/{}/commands/{}/wrappers/{}/launch'.format(project, command_id, wrapper_id)
    with init_session(user, password) as s:
        r = s.post(server + url, data)
        if r.ok:
            return r.json()['container-id']
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: /n {r.text}')

# todo: can I dynamically set soft timeout?
def poll_cs(container_id, xnat_credentials, interval):
    """ Check for completion of a Container Service command

    :param str container_id: the id of the launched container
    :param tuple xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :return: status of the container if the container has terminated, or 'Timed Out' if the container didn't terminate
    in the allotted time
    :rtype: str
    """
    server, user, password = xnat_credentials
    with init_session(user, password) as s:
        while True:
            r = s.get(server + '/xapi/containers/{}'.format(container_id))
            if r.ok:
                status = r.json()['status']
                if status in ['Complete', 'Failed', 'Killed', 'Killed (Out of Memory)']:
                    return status
                time.sleep(interval)
            else:
                raise ValueError(f'Unexpected status code: {r.status_code}  Response: /n {r.text}')

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5}, soft_time_limit=10000)
def poll_cs_dcm2nii(self, container_id, xnat_credentials, interval):
    try:
        return poll_cs(container_id, xnat_credentials, interval)
    except SoftTimeLimitExceeded:
        return 'Timed Out'

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5}, soft_time_limit=259200)
def poll_cs_fsrecon(self, container_id, xnat_credentials, interval):
    try:
        return poll_cs(container_id, xnat_credentials, interval)
    except SoftTimeLimitExceeded:
        return 'Timed Out'


@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def dl_file_from_xnat(self, scan_uri, xnat_credentials, file_path):
    """Download a file from XNAT

    :param self: the task object
    :param str scan_uri: the XNAT uri of the scan to download
    :param tuple xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param str file_path: where to write the file locally
    :return: the name of the file in XNAT
    :rtype: str
    """
    server, user, password = xnat_credentials
    with init_session(user, password) as s:
        r = s.get(server + os.path.join(scan_uri, 'resources', 'NIFTI', 'files'))
        if r.ok:
            result = r.json()['ResultSet']['Result'][0]
            response = s.get(server + result['URI'])
            if response.ok:
                with open(os.path.join(file_path, result['Name']), 'wb') as f:
                    f.write(response.content)
                    return result['Name']
            else:
                raise ValueError(f'Unexpected status code: {response.status_code}  Response: /n {r.text}')
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: /n {r.text}')
    return r




