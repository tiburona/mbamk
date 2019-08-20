import xnat
from .tasks import *
from celery import chain

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

from .tasks import poll_cs_dcm2nii, poll_cs_fsrecon


poll_tasks = {
    'dicom_to_nifti': poll_cs_dcm2nii,
    'freesurfer_recon_all': poll_cs_fsrecon
}

class XNATConnection:

    def __init__(self, config, set_docker_host=False):
        self.xnat_config = config
        self._set_attributes()
        if set_docker_host:
            self._set_docker_host()

    def _set_attributes(self):
        """ Set attributes on self

        Part of the instance initialization, sets XNAT server, user, password, and project, paths to the XNAT archive
        and prearchive, and the destination for uploaded files.

        :return: None
        """
        [setattr(self, k, v) for k, v in self.xnat_config.items()]
        for dest in ['archive', 'prearchive']:
            setattr(self, dest + '_prefix', '/data/{}/projects/{}'.format(dest, self.project))
        self.auth = (self.server, self.user, self.password)


    def _set_docker_host(self):
        """ Set the Docker host
        Reads the desired Docker host from the config file. If XNAT is not currently configured to launch containers on
        this Docker host, configures it so.
        :return: None
        """
        docker_host_route = '/xapi/docker/server'
        if self.xnat_get(docker_host_route).json()['host'] != self.docker_host:
            self.xnat_post(docker_host_route, data={'host':self.docker_host})

    def _command_config(self):
        # check that commands exist on XNAT?  do I really need to do this?
        pass


    def sub_exp_ids(self, user, experiment):
        xnat_ids = self._generate_sub_exp_ids(user, experiment)
        existing_user_ids = self._check_for_existing_user_ids(user)

        return self._merge_ids(xnat_ids, existing_user_ids)

    def _generate_sub_exp_ids(self, user, experiment):
        xnat_ids = {}

        xnat_ids['subject'] = {'xnat_id': str(user.id).zfill(6)}

        xnat_exp_id = '{}_MR{}'.format(xnat_ids['subject']['xnat_id'], user.num_experiments)
        exp_date = experiment.date.strftime('%m/%d/%Y')
        xnat_ids['experiment'] = {'xnat_id': xnat_exp_id,
                                  'query_string': '?xnat:mrSessionData/date={}'.format(exp_date)}

        return xnat_ids

    def _generate_scan_ids(self, experiment,  dcm=False):
        """Generate object ids for use in XNAT

        Creates a dictionary with keys for type of XNAT object, including subject, experiment, scan, resource and file.
        The values in the dictionary are dictionaries with keys 'xnat_id' and, optionally, 'query_string'.  'xnat_id'
        points to the identifier of the object in XNAT, and 'query_string' to the query that will be used in the put
        request to create the object.

        :return: xnat_id dictionary
        :rtype: dict
        """

        xnat_ids = {}

        scan_number = experiment.num_scans + 1
        xnat_scan_id = 'T1_{}'.format(scan_number)
        xnat_ids['scan'] = {'xnat_id': xnat_scan_id, 'query_string': '?xsiType=xnat:mrScanData'}

        if not dcm:
            xnat_ids['resource'] = {'xnat_id': 'NIFTI'}

        return xnat_ids

    def _check_for_existing_user_ids(self, user):
        """Check for existing attributes on the user and experiment

        Generates a dictionary with current xnat_id for the user and the experiment as
        values if they exist (empty string if they do not exist).

        :return: a dictionary with two keys with the xnat subject id and xnat experiment id.
        :rtype: dict
        """

        return {'subject': {key: getattr(user, key) if hasattr(user, key) else {key: ''} for key in ['xnat_id', 'xnat_uri']}}

    def _merge_ids(self, new, existing, levels=['subject'], keys=['xnat_uri', 'xnat_id']):
        for level in levels:
            for key in keys:
                if key in existing:
                    if len(existing[level][key]):
                        new[level][key] = existing[level][key]
        return new

    def upload_scan_file(self, file_path, import_service=False):
        """ Create the XNAT upload chain
        Creates, but does not execute, the Celery chain that creates the XNAT subject and experiment, if necessary, then
        either uploads or imports (for non-dicoms and dicoms, respectively) a dicom file to XNAT.  This chain eventually
        returns the uris for all the created objects.

        :param str file_path:
        :param bool import_service:
        :return: Celery upload chain
        """

        exp_uri, req_url = self._gen_exp_uri_and_req_url

        if import_service:
            upload_task = import_scan_to_xnat
        else:
            upload_task = upload_scan_to_xnat

        upload_signature = upload_task.s(xnat_credentials=self.auth, file_path=file_path)

        get_latest_scan_info_signature = get_latest_scan_info.s(xnat_credentials=self.auth)

        return upload_signature | get_latest_scan_info_signature

    def _gen_exp_uri_and_req_url(self, ids, dcm):
        uri = self.archive_prefix
        url = self.server + uri

        levels = ['subject', 'experiment', 'scan', 'resource']
        if dcm:
            levels = levels[:-2]

        for level in levels:

            addition = os.path.join(level + 's', ids[level]['xnat_id'])

            # Check if a query must be added to the uri
            try:
                query = ids[level]['query_string']
            except KeyError:  # A KeyError will occur when there's no query, which is expected for some levels (like Resource)
                query = ''

            uri = os.path.join(uri, addition)
            if level == 'experiment':
                experiment_uri = uri

            url = os.path.join(url, addition + query)

        if not dcm:
            url = os.path.join(url, 'files')

        return experiment_uri, url

    def launch_and_poll_for_completion(self, process_name, data=None):

        return chain(
            self.launch_command(process_name, data),
            self.poll_container_service(process_name)
        )

    def gen_dicom_conversion_data(self):
        return gen_dicom_conversion_data.s()

    def launch_command(self, process_name, data=None):
        xnat_credentials = (self.server, self.user, self.password)

        if not self.xnat_config['local_docker']:
            process_name += '_transfer'

        command_ids = self.generate_container_service_ids(process_name)

        if data:
            return launch_command.si(data, xnat_credentials, self.project, command_ids)
        else:
            return launch_command.s(xnat_credentials, self.project, command_ids)

    def poll_container_service(self, process_name):

        intervals = {'dicom_to_nifti': 5, 'freesurfer_recon_all': 172800}
        poll_task = poll_tasks[process_name]
        xnat_credentials = (self.server, self.user, self.password)

        return poll_task.s(xnat_credentials, intervals[process_name])

    def dl_file_from_xnat(self, file_depot):
        return dl_file_from_xnat.s(self.auth, file_depot)

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

    def xnat_experiment_uri(self, exp_id):
        return f'/data/experiments/{exp_id}'

    def xnat_subject_uri(self, sub_id):
        return f'/data/subjects/{sub_id}'

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






