import xnat
from .tasks import *
from celery import chain

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"




class XNATConnection:

    def __init__(self, config, set_docker_host=False):
        self.xnat_config = config
        self._set_attributes()
        self.xnat_hierarchy = ['subject', 'experiment', 'scan', 'resource', 'file']
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

    def generate_xnat_identifiers(self, user, experiment, dcm=False):
        """Generate object ids for use in XNAT

        Creates a dictionary with keys for type of XNAT object, including subject, experiment, scan, resource and file.
        The values in the dictionary are dictionaries with keys 'xnat_id' and, optionally, 'query_string'.  'xnat_id'
        points to the identifier of the object in XNAT, and 'query_string' to the query that will be used in the put
        request to create the object.

        :return: xnat_id dictionary
        :rtype: dict
        """
        xnat_ids = {}

        xnat_ids['subject'] = {'xnat_id': str(user.id).zfill(6)}

        xnat_exp_id = '{}_MR{}'.format(xnat_ids['subject']['xnat_id'], user.num_experiments)
        exp_date = experiment.date.strftime('%m/%d/%Y')
        xnat_ids['experiment'] = {'xnat_id': xnat_exp_id,
                                  'query_string': '?xnat:mrSessionData/date={}'.format(exp_date)}

        scan_number = experiment.num_scans + 1
        xnat_scan_id = 'T1_{}'.format(scan_number)
        xnat_ids['scan'] = {'xnat_id': xnat_scan_id, 'query_string': '?xsiType=xnat:mrScanData'}

        if dcm:
            resource = 'DICOM'
        else:
            resource = 'NIFTI'
        xnat_ids['resource'] = {'xnat_id': resource}

        xnat_ids['file'] = {'xnat_id': 'T1.nii.gz', 'query_string': '?xsi:type=xnat:mrScanData'}

        self.xnat_ids = xnat_ids

        self.existing_xnat_ids = self.check_for_existing_xnat_ids(user, experiment)

        return (xnat_ids['subject']['xnat_id'], xnat_ids['experiment']['xnat_id'], xnat_ids['scan']['xnat_id'])

    def check_for_existing_xnat_ids(self, user, experiment):
        """Check for existing attributes on the user and experiment

        Generates a dictionary with current xnat_id for the user and the experiment as
        values if they exist (empty string if they do not exist).

        :return: a dictionary with two keys with the xnat subject id and xnat experiment id.
        :rtype: dict
        """

        objs = {'subject': user, 'experiment': experiment}

        return {k:{'xnat_id': getattr(objs[k], 'xnat_id')} if getattr(objs[k], 'xnat_id') else {'xnat_id': ''} for k in objs}

    def upload_scan_file(self, file_path, import_service=False):
        """ Create the XNAT upload chain
        Creates, but does not execute, the Celery chain that creates the XNAT subject and experiment, if necessary, then
        either uploads or imports (for non-dicoms and dicoms, respectively) a dicom file to XNAT.  This chain eventually
        returns the uris for all the created objects.

        :param dict ids: xnat ids, uris, and query strings for the creation of subjects, experiments, and scans
        :param str file_path:
        :param bool import_service:
        :return: Celery upload chain
        """

        create_resources_signature = create_resources.s(
            xnat_credentials=self.auth,
            ids=(self.xnat_ids, self.existing_xnat_ids),
            levels=self.xnat_hierarchy,
            import_service=import_service,
            archive_prefix=self.archive_prefix,
        )

        if import_service:
            upload_task = import_scan_to_xnat
        else:
            upload_task = upload_scan_to_xnat

        upload_signature = upload_task.s(xnat_credentials=self.auth, file_path=file_path)

        get_latest_scan_info_signature = get_latest_scan_info.s(xnat_credentials=self.auth)

        return create_resources_signature | upload_signature | get_latest_scan_info_signature

    def launch_and_poll_for_completion(self, process_name):

        intervals =  {'dicom_to_nifti_transfer': 5,  'freesurfer_recon_all': 172800}
        interval = intervals[process_name]

        return chain(
            self.gen_dicom_conversion_data(),
            self.launch_command(process_name),
            self.poll_container_service(5)
        )

    def gen_dicom_conversion_data(self):
        return gen_dicom_conversion_data.s()

    def launch_command(self, process_name):
        xnat_credentials = (self.server, self.user, self.password)
        if self.xnat_config['local_docker'] == 'False':
            process_name += '_transfer'
        command_ids = self.generate_container_service_ids(process_name)
        return launch_command.s(xnat_credentials, self.project, command_ids)

    def poll_container_service(self, interval):
        xnat_credentials = (self.server, self.user, self.password)
        return poll_cs.s(xnat_credentials, interval)

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
