import xnat
from cookiecutter_mbam.base import BaseService
from .tasks import *
from celery import chain
from functools import reduce
from flask import current_app


def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


poll_tasks = {
    'dicom_to_nifti': poll_cs_dcm2nii,
    'freesurfer_recon': poll_cs_fsrecon,
    'fs_to_mesh': poll_cs_fs2mesh
}

config_vars = [
    ('server', 'XNAT_HOST'), ('user', 'XNAT_USER'), ('password', 'XNAT_PASSWORD'), ('project', 'XNAT_PROJECT'),
    ('docker_host', 'XNAT_DOCKER_HOST'), ('dicom_to_nifti_wrapper', 'DICOM_TO_NIFTI_WRAPPER'),
    ('dicom_to_nifti_command', 'DICOM_TO_NIFTI_COMMAND'), ('freesurfer_recon_wrapper', 'FREESURFER_RECON_WRAPPER'),
    ('freesurfer_recon_command', 'FREESURFER_RECON_COMMAND'), ('fs_to_mesh_command', 'FS_TO_MESH_COMMAND'),
    ('fs_to_mesh_wrapper', 'FS_TO_MESH_WRAPPER')
]

# todo: arguably there should be two separate classes here, XNAT Connection and XNAT service

class XNATConnection(BaseService):

    def __init__(self):
        self._set_config(config_vars)
        self._set_attributes()

    def _set_attributes(self):
        """ Set attributes on self

        Part of the instance initialization, sets XNAT server, user, password, and project, paths to the XNAT archive
        and prearchive, and the destination for uploaded files.

        :return: None
        """
        for dest in ['archive', 'prearchive']:
            setattr(self, dest + '_prefix', '/data/{}/projects/{}'.format(dest, self.project))
        self.auth = (self.server, self.user, self.password)

    def sub_exp_labels(self, user, experiment):
        """Get the XNAT labels for the subject and the experiment

        :param user: the user
        :type user: cookiecutter_mbam.User
        :param experiment: the experiment
        :type experiment: cookiecutter_mbam.Experiment
        :return: a two-tuple with a dict of subject and experiment labels and a list of keys not yet existing in XNAT
        :rtype: tuple
        """
        xnat_labels = self._generate_sub_exp_labels(user, experiment)
        xnat_labels, not_in_xnat = self._check_for_existing_xnat_labels(user, experiment, xnat_labels)
        return xnat_labels, not_in_xnat

    def _check_for_existing_xnat_labels(self, user, experiment, xnat_labels):
        """Check for existing attributes on the user and experiment

        Generates a dictionary with current xnat_id for the user and the experiment as values if they exist (empty
        string if they do not exist).
        :return: a two-tuple with a dict of subject and experiment labels and a list of keys not yet existing in XNAT
        :rtype: tuple
        """
        objs = {'subject': user, 'experiment': experiment}
        keys = ['xnat_label', 'xnat_uri']

        not_in_xnat = [obj for obj in ['subject', 'experiment'] if not getattr(objs[obj], 'xnat_label')]

        for obj in objs:
            for key in keys:
                if getattr(objs[obj], key):
                    xnat_labels[obj][key] = getattr(objs[obj], key)

        return xnat_labels, not_in_xnat

    def _generate_sub_exp_labels(self, user, experiment):
        """Generate subject and experiment labels for use in XNAT

        Creates a dictionary with keys for type these types XNAT object: subject and experiment.
        The values in the dictionary are dictionaries with keys 'xnat_label' and, optionally, 'query_string'.
        'xnat_label' points to the identifier of the object in XNAT, and 'query_string' to the query that will be used
        in the put request to create the object.

        :param user: the user
        :type user: cookiecutter_mbam.User
        :param experiment: the experiment
        :type experiment: cookiecutter_mbam.Experiment
        :return xnat_labels: a dictionary with the XNAT labels for subject and experiment
        :rtype: dict
        """
        xnat_labels = {'subject': {'xnat_label': str(user.id).zfill(6)}}
        xnat_exp_label = '{}_MR{}'.format(xnat_labels['subject']['xnat_label'], user.experiment_counter)
        exp_date = experiment.date.strftime('%m-%d-%Y')
        xnat_labels['experiment'] = {'xnat_label': xnat_exp_label,
                                     'query_string': '?xnat:mrSessionData/date={}'.format(exp_date)}

        return xnat_labels

    def scan_labels(self, experiment, dcm=False):
        """Generate object labels for use in XNAT

        Creates a dictionary with keys for type these types XNAT object: scan, resource and file.
        The values in the dictionary are dictionaries with keys 'xnat_label' and, optionally, 'query_string'.
        'xnat_label' points to the identifier of the object in XNAT, and 'query_string' to the query that will be used
        in the put request to create the object.

        :return xnat_labels: dictionary of labels in XNAT
        :rtype: dict
        """
        scan_number = experiment.scan_counter
        xnat_scan_label = 'T1_{}'.format(str(scan_number).zfill(2))
        xnat_labels = {'scan': {'xnat_label': xnat_scan_label, 'query_string': '?xsiType=xnat:mrScanData'}}

        if not dcm:
            xnat_labels['resource'] = {'xnat_label': 'NIFTI'}
            xnat_labels['file'] = {'xnat_label': 'T1.nii.gz', 'query_string': '?xsi:type=xnat:mrScanData'}

        return xnat_labels

    def _generate_uris(self, xnat_labels, import_service):
        """Generate paths to XNAT resources for put and post requests

        :param xnat_labels: xnat labels and optionally query strings for each object
        :type xnat_labels: dict
        :param import_service: whether XNAT's import service will ultimately be used in uploading files
        :type import_service: bool
        :return a two-tuple of paths to the resources (without query string) and full url with query string
        :rtype: tuple
        """
        levels = ['subject', 'experiment', 'scan', 'resource', 'file']
        uris = {}
        urls = {}
        uri = self.archive_prefix

        if import_service:
            levels = levels[:-3]

        for level in levels:
            # Construct the uris for each level and add them to the dictionary this task returns
            uri = os.path.join(uri, level + 's', xnat_labels[level]['xnat_label'])
            uris[level] = uri

            # Check if a query must be added to the uri
            try:
                query = xnat_labels[level]['query_string']
            except KeyError:  # A KeyError will occur when there's no query, which is expected for some levels (like Resource)
                query = ''

            url = self.server + uri + query
            urls[level] = url

        return uris, urls

    def _create_resources(self, urls, import_service, first_scan):
        """Create resource objects in XNAT in preparation for uploading the file

        :param urls: the urls to upload for every level
        :type urls: dict
        :param import_service: whether to use XNAT's import service when uploading
        :type import_service: bool
        :param first_scan: whether the scan to be uploaded is the first in a given experiment
        :type first_scan: bool
        :return: a two-tuple with a boolean (whether there are resources to create), and the signature of the task to
        create them (or None if they do not need to be created)
        :rtype: tuple
        """
        resources_to_create = ['subject', 'experiment', 'scan', 'resource']

        if not first_scan:
            resources_to_create = resources_to_create[2:]
        if import_service:
            resources_to_create = resources_to_create[:-2]

        if len(resources_to_create):
            create_resources_signature = create_resources.si(
                xnat_credentials=self.auth,
                to_create=resources_to_create,
                urls=urls
            )
            return (True, create_resources_signature)

        else:
            return (False, None)

    def upload_scan_file(self, file_path, xnat_labels, import_service=False, is_first_scan=True,
                         set_sub_and_exp_attrs=None):
        """ Create the XNAT upload chain
        Creates the Celery chain that creates the XNAT subject and experiment, if necessary, then either uploads or
        imports (for non-dicoms and dicoms, respectively) a dicom file to XNAT.  This chain eventually returns the uris
        for all the created objects.

        :param file_path: the path of the file on the web server
        :type file_path: str
        :param xnat_labels: labels, and sometimes query strings, necessary to construct urls for put and post requests
        :type xnat_labels: dict
        :param bool import_service:
        :return: signature of the Celery upload chain
        :rtype: Celery.canvas._chain
        """
        uris, urls = self._generate_uris(xnat_labels, import_service)

        do_create_resources, create_resources_signature = self._create_resources(urls, import_service, is_first_scan)

        if import_service:
            url = self.server + '/data/services/import'
        else:
            url = urls['file']

        upload_signature = upload_scan_to_xnat.si(
            xnat_credentials=self.auth,
            file_path=file_path,
            url=url,
            exp_uri = uris['experiment'],
            imp = import_service
        )

        get_latest_scan_info_signature = get_latest_scan_info.s(xnat_credentials=self.auth)

        tasks = [(create_resources_signature, do_create_resources),
                 (set_sub_and_exp_attrs, set_sub_and_exp_attrs),
                 (upload_signature, True),
                 (get_latest_scan_info_signature, True)]

        upload_chain = reduce((lambda x, y: chain(x, y)), [task for task, perform_task in tasks if perform_task])

        return upload_chain

    def launch_and_poll_for_completion(self, process_name, data=None):
        """Construct a Celery chain to launch an XNAT container and poll for its completion

        :param process_name: an identifier for the process
        :type process_name: str
        :param data: data to provide with the post request that launches a container via the XNAT container service
        :type data: Union([dict, None])
        :return: signature of the Celery chain
        :rtype: Celery.canvas._chain
        """
        return chain(
            self.launch_command(process_name, data),
            self.poll_container_service(process_name)
        )

    def gen_container_data(self, download_suffix, upload_suffix, uri=None):
        """Get the signature for the Celery task that gerates the data needed to launch an XNAT container

        :param download_suffix: the path on XNAT where the input is
        :type download_suffix: str
        :param upload_suffix: the path on XNAT to which output will be uploaded
        :type upload_suffix: str
        :return: signature of the Celery task to generate data
        :rtype: celery.canvas.Signature
        """
        if uri:
            return gen_container_data.si(uri, self.auth, download_suffix, upload_suffix)
        else:
            return gen_container_data.s(self.auth, download_suffix, upload_suffix)

    def launch_command(self, process_name, data=None):
        """Generate the signature to launch a command with the XNAT container service

        :param process_name: an identifier for the process
        :type process_name: str
        :param data: data to provide with the post request that launches a container via the XNAT container service
        :type data: Union([dict, None])
        :return: signature of the Celery task to launch a command
        :rtype: celery.canvas.Signature
        """
        xnat_credentials = (self.server, self.user, self.password)

        command_ids = getattr(self, process_name + '_command'), getattr(self, process_name + '_wrapper')

        if data:
            return launch_command.si(data, xnat_credentials, self.project, command_ids)
        else:
            return launch_command.s(xnat_credentials, self.project, command_ids)

    #todo: restore freesurfer interval after testing!
    def poll_container_service(self, process_name):
        """Generate the signature of the Celery task that polls the container service to check for completion

        :param process_name: an identifier for the process
        :type process_name: str
        :return: signature of the Celery task to poll the container service
        :rtype: celery.canvas.Signature
        """

        intervals = {'dicom_to_nifti': 5, 'freesurfer_recon': 5, 'fs_to_mesh': 5}
        poll_task = poll_tasks[process_name]
        xnat_credentials = (self.server, self.user, self.password)
        return poll_task.s(xnat_credentials, intervals[process_name])

    def dl_files_from_xnat(self, file_depot, suffix='', single_file=True, conditions=None):
        """Generate the signature of the Celery task to download files from XNAT

        :param file_depot: repository for downloaded files on the web server
        :type file_depot: str
        :param suffix: suffix to attach to XNAT URI in order to locate the files to download (the URI is passed by the
        previous task)
        :type suffix: str
        :param single_file: whether to download a single file or more than one
        :type single_file: bool
        :param conditions: a list of conditions, in the form of keys to a dict where vals are anonymous functions, to
        place on the result of a get request -- if the conditions aren't met the file isn't downloaded
        :return: signature of the Celery task to download a file from XNAT
        :rtype: celery.canvas.Signature
        """
        return dl_files_from_xnat.s(self.auth, file_depot, suffix=suffix, single_file=single_file,
                                    conditions=conditions)

    # todo: add error handling to this and subsequent CRUD method wrappers for XNAT
    def xnat_get(self, url):
        """Get a resource from XNAT
        :param url: the url (minus the server) of the resource you're interested in getting from the XNAT API
        :type url: str
        :return: the response to the request
        :rtype: requests.Response
        """
        with init_session(self.user, self.password) as session:
            return session.get(self.server + url)

    def xnat_put(self, url):
        """Put a resource to XNAT
        :param url: the url (minus the server) of the resource you're interested in putting to the XNAT API
        :type url: str
        :return: the response to the request
        :rtype: requests.Response
        """
        with init_session(self.user, self.password) as session:
            try:
                return session.put(self.server + url)
            except Exception as e:
                pass

    def xnat_post(self, url, data=None):
        """Put a resource to XNAT
        :param url: the url (minus the server) of the resource you're interested in putting to the XNAT API
        :type url: str
        :return: the response to the request
        :rtype: requests.Response
        """
        with init_session(self.user, self.password) as session:
            return session.post(self.server + url, data=data)

    def xnat_delete(self, url):
        """ Delete an item from XNAT

        :param url: The REST path of the resource to delete
        :type url: str
        :return: None
        """
        try:
            with xnat.connect(self.server, self.user, self.password) as session:
                session.delete(url)
        except:
            # todo: handle errors!
            pass

    def refresh_xnat_catalog(self, resource_url):
        if resource_url[:5] == '/data':
            resource_url = resource_url[5:]
        refresh_url = '/data/services/refresh/catalog?resource=' + resource_url
        return self.xnat_post(refresh_url)
