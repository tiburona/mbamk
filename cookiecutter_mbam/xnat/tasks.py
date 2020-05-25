import time
import os
import shutil
from celery.exceptions import SoftTimeLimitExceeded
from cookiecutter_mbam import celery
from cookiecutter_mbam.utils.request_utils import init_session

@celery.task
def create_resources(xnat_credentials, to_create, urls):
    """ Create XNAT resources (subject, experiment, scan, resource) as necessary

    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :type xnat_credentials: tuple
    :param to_create: the levels (among subject, experiment, scan, resource) that should be created
    :type to_create: list
    :param urls: a dictionary of urls for each put request
    :type urls: dict
    :return: a dictionary of the values XNAT returned for subject and experimenet id
    :rtype: dict
    """
    server, user, password = xnat_credentials

    responses = {}

    with init_session(user, password) as s:
        print("Using XNAT server {}".format(server))
        for level in to_create:
            url = urls[level]
            r = s.put(url)

            print(url)

            if level in ['subject', 'experiment']:
                responses[level] = r.text

            if not r.ok:
                raise ValueError(f'Unexpected status code: {r.status_code} Response: \n {r.text}')

    return responses

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def upload_scan_to_xnat(self, xnat_credentials, file_path, url, exp_uri, imp, delete=True):
    """ Upload a NIFTI format scan to XNAT
    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :type xnat_credentials: tuple
    :param file_path: where to find the file on the local server
    :param url: the path in the API to put or post the file to
    :type url: str
    :param exp_uri: the uri of the experiment in XNAT, used as data for the import service
    :type exp_uri: str
    :param imp: whether to use XNAT's import service to upload the file
    :type imp: bool
    :return: uris
    """

    server, user, password = xnat_credentials

    filename = 'T1.zip' if imp else 'T1.nii.gz'
    kwargs = {'files': {'file': (filename, open(file_path, 'rb'), 'application/octet-stream')}}
    if imp: kwargs['data'] = {'dest': exp_uri, 'overwrite': 'delete'}

    with init_session(user, password) as s:
        if imp:
            r = s.post(url, **kwargs)
        else:
            r = s.put(url, **kwargs)

        if delete:
            shutil.rmtree(os.path.dirname(file_path),ignore_errors=True)

        if r.ok:
            return exp_uri
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: \n {r.text}')

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def get_latest_scan_info(self, experiment_uri, xnat_credentials):
    """ Get XNAT URI and id of the last uploaded scan for the current experiment

     XNAT automatically sets the ID of an imported scan and MBAM makes no attempt to overwrite it.  This function
     retrieves that information (regardless of whether the scan was uploaded or imported.)

    :param uris: a dictionary with levels as keys that contains the experiment uri
    :type uris: dict
    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :type xnat_credentials: tuple
    :return: a dictionary of the XNAT id and XNAT URI of the scan
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
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: \n {r.text}')

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def gen_container_data(self, uri, xnat_credentials, download_suffix, upload_suffix):
    """Generate the data necessary to launch a command in XNAT
    :param uri: URI of the resource, minus the suffix that indicates the specific URI for file download
    :param uri: str
    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :type xnat_credentials: tuple
    :param download_suffix: the suffix that, concatenated with `uri`, indicates the URI for file download
    :type download_suffix: str
    :param upload_suffix: the sufficx that, concatenated with `uri`, indicates where to upload processed files
    :type upload_suffix: str
    :return: the data that will be passed to the container via a post request
    :rtype: dict
    """
    server, _, _ = xnat_credentials
    return {
        'download-url': server + uri + download_suffix,
        'upload-url': server + uri + upload_suffix,
        'xnat-host': server
    }


@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def launch_command(self, data, xnat_credentials, project, command_ids):
    """ Launch a command in XNAT
    :param data: the payload to be included with the post request to launch the command
    :type data: dict
    :param project: the XNAT project
    :type project: str
    :param command_ids: a two-tuple of the command id and the id of the wrapper in the XNAT host executing the command
    :type command_ids: tuple
    :return: container id
    :rtype: str
    """
    server, user, password = xnat_credentials
    command_id, wrapper_id = command_ids
    url = '/xapi/projects/{}/commands/{}/wrappers/{}/launch'.format(project, command_id, wrapper_id)
    with init_session(user, password) as s:
        r = s.post(server + url, data)
        if r.ok:
            return construct_container_data(r.json(), server)
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: \n {r.text}')


def construct_container_data(r_json, server):
    """Take the response from the XNAT container service to launching a container and extract data from it
    :param r_json: the json data from the response from the containre service
    :type r_json: dict
    :param server: the XNAT host
    :type server: str
    :return container_data: a selection of data returned from the post request to launch the container
    :rtype: dict
    """
    container_key = 'container-id' if 'container-id' in r_json else 'service-id'
    container_data = {k: r_json[k] for k in [container_key, 'id']}
    for new, old in [('cs_id', 'id'), ('xnat_container_id', container_key)]:
        container_data[new] = container_data.pop(old)
    container_data['xnat_host'] = server
    return container_data


def poll_cs(container_info, xnat_credentials, interval):
    """ Check for completion of a container service command
    :param container_info: information about the launched container, passed from the previous Celery task
    :type container_info: dict
    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param interval: how long to wait between efforts to poll the container service for container completion
    :type interval: none
    :return: status of the container if the container has terminated
    :rtype: str
    """

    server, user, password = xnat_credentials
    container_id = container_info['xnat_container_id']

    with init_session(user, password) as s:
        while True:
            r = s.get(server + '/xapi/containers/{}'.format(container_id))
            if r.ok:
                status = r.json()['status']
                if status in ['Complete', 'Failed', 'Killed', 'Killed (Out of Memory)']:
                    # Todo: is this really correctly returning when 'Failed'?
                    # Todo: write logic to check for rejected container
                    return status
                time.sleep(interval)
            else:
                raise ValueError(f'Unexpected status code: {r.status_code}  Response: \n {r.text}')

# These and the two following tasks must be defined separately because the soft_time_limit must be defined in the
# wrapper arguments, but #todo: make sure there's no way around this.
@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5}, soft_time_limit=10000)
def poll_cs_dcm2nii(self, container_id, xnat_credentials, interval):
    """Check for completion of a dcm2nii command
    :param container_id: the id of the container
    :type container_info: str
    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param interval: how long to wait between efforts to poll the container service for container completion
    :type interval: int
    :return: status of the container if the container has terminated, or 'Timed Out' if the container didn't terminate
    in the allotted time
    :rtype: str
    """
    try:
        return poll_cs(container_id, xnat_credentials, interval)
    except SoftTimeLimitExceeded:
        return 'Timed Out'


@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5}, soft_time_limit=259200)
def poll_cs_fsrecon(self, container_id, xnat_credentials, interval):
    """Check for completion of the Freesurfer recon command
    :param container_id: the id of the container
    :type container_info: str
    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param interval: how long to wait between efforts to poll the container service for container completion
    :type interval: int
    :return: status of the container if the container has terminated, or 'Timed Out' if the container didn't terminate
    in the allotted time
    :rtype: str
    """
    try:
        return poll_cs(container_id, xnat_credentials, interval)
    except SoftTimeLimitExceeded:
        return 'Timed Out'

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5}, soft_time_limit=259200)
def poll_cs_fs2mesh(self, container_id, xnat_credentials, interval):
    """Check for completion of the Freesurfer to 3D mesh command
    :param container_id: the id of the container
    :type container_info: str
    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :param interval: how long to wait between efforts to poll the container service for container completion
    :type interval: int
    :return: status of the container if the container has terminated, or 'Timed Out' if the container didn't terminate
    in the allotted time
    :rtype: str
    """
    try:
        return poll_cs(container_id, xnat_credentials, interval)
    except SoftTimeLimitExceeded:
        return 'Timed Out'


@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def dl_files_from_xnat(self, uri, xnat_credentials, file_path, suffix='', single_file=True, conditions=None):
    """Download a file from XNAT

    :param uri: the XNAT URI of the resource to download
    :type uri: str
    :param xnat_credentials: a three-tuple of the server, username, and password to log into XNAT
    :type xnat_credentials: tuple
    :param file_path: where to write the file locally
    :type file_path: str
    :param suffix: what to append to the URI to get the full path to the files
    :type suffix: str
    :param single_file: whether to download one file or more than one
    :type single_file: bool
    :param conditions: keys to the dl_conditions dictionary which contains anonymous functions that place conditions on
    downloading a file
    :type conditions: Union([list, NoneType])
    :return: the name of the file in XNAT, or a list of names if there was more than one file
    :rtype: Union([str, list])
    """

    if not os.path.isdir(file_path):
        os.makedirs(file_path)

    server, user, password = xnat_credentials
    if not conditions: conditions = []

    with init_session(user, password) as s:
        r = s.get(server + uri + suffix)
        if r.ok:
            results = [result for result in r.json()['ResultSet']['Result']
                       if all([dl_conditions[condition](result) for condition in conditions])]
            for result in results:
                response = s.get(server + result['URI'])
                if response.ok:
                    with open(os.path.join(file_path, result['Name']), 'wb') as f:
                        f.write(response.content)
                else:
                    raise ValueError(f'Unexpected status code: {response.status_code}  Response: /n {r.text}')
            if single_file:
                return results[0]['Name']
            else:
                return [result['Name'] for result in results]
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}  Response: \n {r.text}')
    return r


dl_conditions={
    'json_exclusion': lambda result: 'json' not in result['Name']
}
