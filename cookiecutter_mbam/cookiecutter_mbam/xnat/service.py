import os

import xnat
import requests
from flask import current_app

from cookiecutter_mbam.utility.celery_utils import get_celery_worker_status
from .tasks import *


#
# celery questions: how do I get these tasks sent to two different workers
# i.e. how to I make sure they're distributed
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


# todo: error handling around the put statement; do we want to log responses from xnat


class XNATConnection:

    def __init__(self, config):
        self.xnat_config = config
        self._set_attributes()
        self.xnat_hierarchy = ['subject', 'experiment', 'scan', 'resource', 'file']
        self.celery_upload = False
        self.celery_import = False
        try:
            self._get_celery_status()
        except:
            # log the exception
            pass

        # Do I want to set Docker's server in response to config?
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
        docker_host_route = '/xapi/docker/server'
        if self.xnat_get(docker_host_route).json()['host'] != self.docker_host:
            self.xnat_post(docker_host_route, data={'host':self.docker_host})

    # Todo: This will almost certainly need to change in a production environment.
    # It's hard to say exactly how without seeing exactly what is returned from worker inspection in a prod env.
    def _get_celery_status(self):
        celery_status = get_celery_worker_status(celery)
        registered_tasks = celery_status['registered_tasks']
        if registered_tasks:
            for key in registered_tasks:
                for task in registered_tasks[key]:
                    if 'import_scan_to_xnat' in task:
                        self.celery_import = True
                    if 'upload_scan_to_xnat' in task:
                        self.celery_upload = True

    def _command_config(self):
        # check that commands exist on XNAT?  do I really need to do this?
        pass

    # todo: what do we want from the response object?  to log it?
    def _upload_file(self, url, file_path):
        if self.celery_upload:
            result = celery_upload.delay(self.server, self.user, self.password, url, file_path)
            result.wait()
        else:
            with xnat.connect(self.server, self.user, self.password) as session:
                result = session.upload(url, file_path)
        return result

    def _import_file(self, file_path, url, **kwargs):
        if self.celery_import:
            url = url[url.find('/archive'):]
            result = import_scan_to_xnat.delay(self.server, self.user, self.password, file_path, url)
            result.wait()
        else:
            with xnat.connect(self.server, self.user, self.password) as session:
                result = session.services.import_(file_path, overwrite='delete', **kwargs)
        return result

    def xnat_get(self, url):
        with init_session(self.user, self.password) as session:
            return session.get(self.server + url)

    def xnat_put(self, url):
        with init_session(self.user, self.password) as session:
            try:
                return session.put(self.server + url)
            except xnat.exceptions.XNATResponseError as e:
                error = e
                if 'status 409' in error.args[0]:  # this error is raised when you try to create a resource that exists
                    return 'You tried to create something that already exists.'
                else:
                    pass
                    # error is unknown, handle it somehow
            return ''

    def xnat_post(self, url, data=None):
        with init_session(self.user, self.password) as session:
            return session.post(self.server + url, data=data)

    def nifti_files_url(self, scan_uri):
        return self.server + os.path.join(scan_uri, 'resources', 'NIFTI', 'files')

    def _fetch_uris(self, subject_uri, experiment_uri):
        new_uris = [self.xnat_get(orig_uri).json()['URI'] for orig_uri in [subject_uri, experiment_uri]]
        scans = self.xnat_get(self.server + self.experiment_uri + '/scans')
        debug()
        return new_uris

        # Here I have just uploaded a scan.
        # Ways I can tell what the most recent scan is:
        # I should know its unique xnat identifier, but in practice I don't unless I figure out how to set this
        # when using the import service
        # does scan have a created by attribute?
        # experiment and subject uri I should be able to fetch by their xnat_id.  if I can get the resource for each of them
        # I can take response.json()['URI']

    def get_scan_info(self, scan_id='latest'):
        subject_id = self.xnat_ids['subject']['xnat_id']
        experiment_id = self.xnat_ids['experiment']['xnat_id']
        with xnat.connect(self.server, self.user, self.password) as session:
            project = session.projects[self.project]
            subject = session.subjects[subject_id]
            experiment = project.experiments[experiment_id]
            if scan_id == 'latest':
                scan = session.projects[self.project].experiments[experiment_id].scans[-1]
            else:
                scan = experiment.scans[scan_id]
        return (project, subject, experiment, scan)

    def get_files(self, scan_id='latest'):
        project, subject, experiment, scan = self.get_scan_info(scan_id=scan_id)
        files = scan.files.values()
        return files

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

    def launch_command(self, command_id, wrapper_id, data=None):
        """
        :param command_id:
        :param wrapper_id:
        :param data:
        :return:
        """
        url =  '/xapi/projects/{}/commands/{}/wrappers/{}/launch'.format(self.project, command_id, wrapper_id)
        return self.xnat_post(url, data)

    def refresh_xnat_catalog(self, resource_url):
        if resource_url[:5] == '/data':
            resource_url = resource_url[5:]
        refresh_url = '/data/services/refresh/catalog?resource=' + resource_url
        return self.xnat_post(refresh_url)

    def upload_chain(self, ids, file_path, import_service=False):
        create_resources_signature = create_resources.s(xnat_credentials = self.auth, ids = ids,
                                                        levels = self.xnat_hierarchy, import_service = import_service,
                                                        archive_prefix = self.archive_prefix)
        if not import_service:
            upload_signature = upload_scan_to_xnat.s(xnat_credentials = self.auth, file_path = file_path)
        else:
            upload_signature = import_scan_to_xnat.s(xnat_credentials = self.auth, file_path = file_path)

        get_uris_signature = get_uris.s(xnat_credentials=self.auth)

        return create_resources_signature | upload_signature | get_uris_signature


    def _generate_ids(self, process_name):
        return (
            self.xnat_config[process_name + '_command_id'],
            self.xnat_config[process_name + '_wrapper_id']
        )


    def upload_scan(self, xnat_ids, existing_xnat_ids, file_path, import_service=False):
        """The method to upload a scan to XNAT

        Iteratively constructs the uris for subject and experiment (if they do not exist).  Constructs the uris for scan,
        resource, and file (if not using the import service).  Calls xnat_put on the generated uris to create objects if
        they do not exist.  Calls xnat_put with a file to upload it, invoking the import service if it is a zip file.
        Returns uris for subject, experiment, and scan so they can be attached to their database objects.

        :param dict xnat_ids: a dictionary of xnat identifiers and query strings for put urls
        :param dict existing_xnat_ids: a dictionary of XNAT identifiers that already existed on user and experiment
        :param str file_path: local path to the file to upload
        :param bool import_service: whether to use the XNAT import service. True if file is a .zip, default False.
        :return: three-tuple of the xnat uris for subject, experiment, and scan
        :rtype: tuple
        """

        self.xnat_ids = xnat_ids
        uri = self.archive_prefix # todo: decide whether to use prearchive
        uris = {}

        if import_service:
            levels = self.xnat_hierarchy[:-3]
        else:
            levels = self.xnat_hierarchy

        for level in levels:
            id = 'xnat_{}_id'.format(level)
            exists_already = id in existing_xnat_ids and len(existing_xnat_ids[id])
            if exists_already:
                uri = os.path.join(uri, level + 's', existing_xnat_ids[id])
            else:
                uri = os.path.join(uri, level + 's', xnat_ids[level]['xnat_id'])

            uris[level] = uri

            try:
                query = xnat_ids[level]['query_string']
            except: # todo specify KeyError here?
                query = ''

            if level == 'file':
                result = self._upload_file(url=uri+query, file_path=file_path)
            else:
                if not exists_already: self.xnat_put(url=uri + query)

        kwargs = {'project': self.project, 'subject': self.xnat_ids['subject']['xnat_id'],
                  'experiment': self.xnat_ids['experiment']['xnat_id']}

        if import_service:
            result = self._import_file(file_path, uri, **kwargs)

        return self._fetch_uris(uris['subject'], uris['experiment'])



