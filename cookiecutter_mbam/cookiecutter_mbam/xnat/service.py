import os
import xnat
from flask import Flask
import requests
from cookiecutter_mbam.tasks import make_celery, get_celery_worker_status


from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

flask_app = Flask(__name__)
celery = make_celery(flask_app)

# todo: error handling around the put statement; do we want to log responses from xnat

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

@celery.task
def celery_upload(server, user, password, url, file_path):
    files = {'file': ('T1.nii.gz', open(file_path, 'rb'), 'application/octet-stream')}
    s = init_session(user, password)
    r = s.put(server + url, files=files)
    return r

@celery.task
def celery_import(server, user, password, file_path, url):
    files = {'file': ('DICOMS.zip', open(file_path, 'rb'), 'application/octet-stream')}
    s = init_session(user, password)
    r = s.post(server + '/data/services/import', files=files, data={'dest': url, 'overwrite':'delete'})
    return r

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
            result = celery_upload(self.server, self.user, self.password, url, file_path)
        else:
            with xnat.connect(self.server, self.user, self.password) as session:
                result = session.upload(url, file_path)
        return result

    def _import_file(self, file_path, url, **kwargs):
        if self.celery_import:
            url = url[url.find('/archive'):]
            result = celery_import(self.server, self.user, self.password, file_path, url, overwrite='delete')
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
        with xnat.connect(self.server, self.user, self.password) as session:
            try:
                response = session.get(url)
            except:
                pass
            return response

    def _fetch_uris(self):
        """
        :param session: the xnatpy XNAT connection object
        :return: the uri of the last created scan
        :rtype: str
        """
        subject_id = self.xnat_ids['subject']['xnat_id']
        experiment_id = self.xnat_ids['experiment']['xnat_id']
        _, subject, experiment, scan = self.get_scan_info(subject_id, experiment_id)
        return (subject.uri, experiment.uri, scan.uri)

    def get_scan_info(self, subject_id, experiment_id):
        with xnat.connect(self.server, self.user, self.password) as session:
            project = session.projects[self.project]
            subject = session.subjects[subject_id]
            experiment = project.experiments[experiment_id]
            scan = session.projects[self.project].experiments[experiment_id].scans[-1]
        return (project, subject, experiment, scan)

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



