import os
import xnat

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

# todo: error handling around the put statement; do we want to log responses from xnat
#

class XNATConnection:

    def __init__(self, config):
        self.xnat_config = config
        self._set_attributes()
        self.xnat_hierarchy = ['subject', 'experiment', 'scan', 'resource', 'file']

    def _set_attributes(self):
        """ Set attributes on self

        Part of the instance initialization, sets XNAT server, user, password, and project, paths to the XNAT archive
        and prearchive, and the destination for uploaded files.

        :return: None
        """
        [setattr(self, k, v) for k, v in self.xnat_config.items()]
        for dest in ['archive', 'prearchive']:
            setattr(self, dest + '_prefix', '/data/{}/projects/{}'.format(dest, self.project))


    # todo: wrap everything in a try/except again
    # what do we want from the response object?  to log it?
    def _xnat_put(self, url='', file_path=None, imp=False, **kwargs):
        """ The method to create an XNAT object

        Uses the xnatpy session.put, session.upload, or session.services.import_ method to add an object to XNAT.

        :param str url: a put route in the XNAT API
        :param str file_path: path to a file to upload
        :param bool imp: whether to use the import service (True if file is zip of dicoms, otherwise False)
        :param kwargs kwargs: arguments to pass to the import service (project, subject, and experiment)
        :return: str the XNAT URI of the created scan, if the import service was invoked, or else an empty string
        """
        with xnat.connect(self.server, self.user, self.password) as session:
            if imp:
                session.services.import_(file_path, overwrite='delete', **kwargs)
                return self._get_uris()
            elif file_path:
                session.upload(url, file_path)
                return self._get_uris()
            else:
                try:
                    response = session.put(url)
                    return response
                except:
                    pass
                    #xnat.exceptions.XNATResponseError as e:
                    # error = e
                    # if 'status 409' in error.args[0]: # this error is raised when you try to create a resource that exists
                    #     pass
                    # else:
                    #     # error is unknown, handle it somehow
            return ''

    def xnat_get(self, url):
        with xnat.connect(self.server, self.user, self.password) as session:
            try:
                response = session.get(url)
            except:
                pass
            return response


    def _get_uris(self):
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
                fetched_uris = self._xnat_put(url=uri + query, file_path=file_path)
            else:
                if not exists_already: self._xnat_put(url=uri + query)

        kwargs = {'project': self.project, 'subject': self.xnat_ids['subject']['xnat_id'],
                  'experiment': self.xnat_ids['experiment']['xnat_id']}

        if import_service:
            fetched_uris = self._xnat_put(file_path=file_path, imp=True, **kwargs)

        return fetched_uris



