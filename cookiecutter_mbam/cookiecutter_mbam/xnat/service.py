import os

import xnat
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

    # Todo: This will almost certainly need to change in a production environment.
    # It's hard to say exactly how without seeing exactly what is returned from worker inspection in a prod env.
    def _get_celery_status(self):
        celery_status = get_celery_worker_status(celery)
        registered_tasks = celery_status['registered_tasks']
        for key in registered_tasks:
            for task in registered_tasks[key]:
                if 'celery_import' in task:
                    self.celery_import = True
                if 'celery_upload' in task:
                    self.celery_upload = True

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
            result = celery_import.delay(self.server, self.user, self.password, file_path, url)
            result.wait()
        else:
            with xnat.connect(self.server, self.user, self.password) as session:
                result = session.services.import_(file_path, overwrite='delete', **kwargs)
        return result


    def xnat_put(self, url):
        with xnat.connect(self.server, self.user, self.password) as session:
            try:
                response = session.put(url)
                return response
            except xnat.exceptions.XNATResponseError as e:
                error = e
                if 'status 409' in error.args[0]:  # this error is raised when you try to create a resource that exists
                    return 'You tried to create something that already exists.'
                else:
                    pass
                    # error is unknown, handle it somehow
            return ''

    def xnat_get(self, url):
        with init_session(self.user, self.password) as session:
            return session.get(self.server + url)

    def nifti_files_url(self, scan):
        return self.server + os.path.join(scan.xnat_uri, 'resources', 'NIFTI', 'files')

    def download_file(self, scan_uri, resource_type, file_obj=True, file_path='', file_name=''):
        response = self.xnat_get(os.path.join(scan_uri, 'resources', resource_type, 'files'))
        if response.ok:
            result =  json.loads(response.text)['ResultSet']['Result'][0]
            response = self.xnat_get(result['URI'])
            if response.ok:
                if file_obj:
                    f_o = BytesIO(response.content)
                    f_o.name = result['Name']
                    return f_o
                with open(os.path.join(file_path, file_name), 'wb') as f:
                    f.write(response.content)
        return response

    def _fetch_uris(self):
        """
        :param session: the xnatpy XNAT connection object
        :return: the uris of the subject, experiment, and last created scan
        :rtype: tuple
        """
        _, subject, experiment, scan = self.get_scan_info()
        return (subject.uri, experiment.uri, scan.uri)

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

    def xnat_post(self, url, data=None):
        with xnat.connect(self.server, self.user, self.password) as session:
            response = session.post(url, data=data)
            return response

    def launch_command(self, command_id, wrapper_id, data=None):
        url =  '/xapi/projects/{}/commands/{}/wrappers/{}/launch'.format(self.project, command_id, wrapper_id)
        return self.xnat_post(url, data)

    def refresh_xnat_catalog(self, resource_url):
        if resource_url[:5] == '/data':
            resource_url = resource_url[5:]
        refresh_url = '/data/services/refresh/catalog?resource=' + resource_url
        return self.xnat_post(refresh_url)

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

        return self._fetch_uris()



