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
    'freesurfer_recon_all': poll_cs_fsrecon
}

config_vars = [
    ('server', 'XNAT_HOST'), ('user', 'XNAT_USER'), ('password', 'XNAT_PASSWORD'), ('project', 'XNAT_PROJECT'),
    ('docker_host', 'XNAT_DOCKER_HOST'), ('dicom_to_nifti_wrapper', 'DICOM_TO_NIFTI_WRAPPER'),
    ('dicom_to_nifti_command', 'DICOM_TO_NIFTI_COMMAND'), ('freesurfer_recon_wrapper', 'FREESURFER_RECON_WRAPPER'),
    ('freesurfer_recon_command', 'FREESURFER_RECON_COMMAND')
]

#todo: arguably there should be two separate classes here, XNAT Connection and XNAT service

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
        xnat_labels = self._generate_sub_exp_labels(user, experiment)
        not_in_xnat = self._check_for_existing_xnat_labels(user, experiment, xnat_labels)

        return xnat_labels, not_in_xnat

    def _check_for_existing_xnat_labels(self, user, experiment, xnat_labels):
        """Check for existing attributes on the user and experiment
        Generates a dictionary with current xnat_id for the user and the experiment as
        values if they exist (empty string if they do not exist).
        :return: a dictionary with two keys with the xnat subject id and xnat experiment id.
        :rtype: dict
        """

        objs = {'subject': user, 'experiment': experiment}
        keys = ['xnat_label', 'xnat_uri']

        not_in_xnat = [obj for obj in ['subject', 'experiment'] if not getattr(objs[obj], 'xnat_label')]

        for obj in objs:
            for key in keys:
                if getattr(objs[obj], key):
                    xnat_labels[obj][key] = getattr(objs[obj], key)

        return not_in_xnat


    def _generate_sub_exp_labels(self, user, experiment):
        xnat_labels = {}

        xnat_labels['subject'] = {'xnat_label': str(user.id).zfill(6)}

        xnat_exp_label = '{}_MR{}'.format(xnat_labels['subject']['xnat_label'], user.experiment_counter)
        exp_date = experiment.date.strftime('%m-%d-%Y')
        xnat_labels['experiment'] = {'xnat_label': xnat_exp_label,
                                  'query_string': '?xnat:mrSessionData/date={}'.format(exp_date)}

        return xnat_labels

    def scan_labels(self, experiment, dcm=False):
        """Generate object ids for use in XNAT

        Creates a dictionary with keys for type of XNAT object, including subject, experiment, scan, resource and file.
        The values in the dictionary are dictionaries with keys 'xnat_id' and, optionally, 'query_string'.  'xnat_id'
        points to the identifier of the object in XNAT, and 'query_string' to the query that will be used in the put
        request to create the object.

        :return: xnat_id dictionary
        :rtype: dict
        """

        xnat_labels = {}

        scan_number = experiment.scan_counter
        xnat_scan_label = 'T1_{}'.format(str(scan_number).zfill(2))
        xnat_labels['scan'] = {'xnat_label': xnat_scan_label, 'query_string': '?xsiType=xnat:mrScanData'}

        if not dcm:
            xnat_labels['resource'] = {'xnat_label': 'NIFTI'}
            xnat_labels['file'] = {'xnat_label': 'T1.nii.gz', 'query_string': '?xsi:type=xnat:mrScanData'}

        return xnat_labels


    def _generate_uris(self, xnat_labels, import_service):
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
        Creates, but does not execute, the Celery chain that creates the XNAT subject and experiment, if necessary, then
        either uploads or imports (for non-dicoms and dicoms, respectively) a dicom file to XNAT.  This chain eventually
        returns the uris for all the created objects.

        :param str file_path:
        :param bool import_service:
        :return: Celery upload chain
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

        return chain(
            self.launch_command(process_name, data),
            self.poll_container_service(process_name)
        )

    def gen_container_data(self, download_suffix, upload_suffix, uri=None):
        if uri:
            return gen_container_data.si(uri, self.auth, download_suffix, upload_suffix)
        else:
            return gen_container_data.s(self.auth, download_suffix, upload_suffix)

    def launch_command(self, process_name, data=None):
        xnat_credentials = (self.server, self.user, self.password)

        if not self.xnat_config['local_docker']:
            process_name += '_transfer'

        command_ids = self.generate_container_service_ids(process_name)

        if data:
            return launch_command.si(data, xnat_credentials, self.project, command_ids)
        else:
            return launch_command.s(xnat_credentials, self.project, command_ids)


    #todo: restore freesurfer interval after testing!
    def poll_container_service(self, process_name):

        intervals = {'dicom_to_nifti': 5, 'freesurfer_recon_all': 5}
        poll_task = POLL_TASKS[process_name]
        xnat_credentials = (self.server, self.user, self.password)

        return poll_task.s(xnat_credentials, intervals[process_name])

    def dl_files_from_xnat(self, file_depot, suffix='', single_file=True, conditions=[]):
        return dl_files_from_xnat.s(self.auth, file_depot, suffix=suffix, single_file=single_file, conditions=conditions)

    def generate_container_service_ids(self, process_name):
        return (
            self.xnat_config[process_name + '_command_id'],
            self.xnat_config[process_name + '_wrapper_id']
        )

    def xnat_get(self, url):
        """Get a resource from XNAT
        Gets a resource from the XNAT API.  In case of error, should catch the exception, return it, and log it.
        :param str url: the url (minus the server) of the resource you're interested in getting from the XNAT api
        :return: the response to the request
        """
        with init_session(self.user, self.password) as session:
            return session.get(self.server + url)

    def xnat_put(self, url):
        with init_session(self.user, self.password) as session:
            try:
                return session.put(self.server + url)
            except Exception as e:
                pass

    def xnat_post(self, url, data=None):
        with init_session(self.user, self.password) as session:
            return session.post(self.server + url, data=data)

    def xnat_delete(self, url):
        """ Delete an item from XNAT

        Deletes an item from XNAT.

        :param url: The REST path of the resource to delete
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






