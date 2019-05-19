import xnat
from .tasks import *
from cookiecutter_mbam.utility.celery_utils import log_error, send_email

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


# todo: error handling!


class XNATConnection:

    def __init__(self, config):
        self.xnat_config = config
        self._set_attributes()
        self.xnat_hierarchy = ['subject', 'experiment', 'scan', 'resource', 'file']
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

    def upload_chain(self, ids, file_path, import_service=False):
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
            ids=ids,
            levels=self.xnat_hierarchy,
            import_service=import_service,
            archive_prefix=self.archive_prefix,
        )

        if import_service:
            upload_task = import_scan_to_xnat
        else:
            upload_task = upload_scan_to_xnat

        upload_signature = upload_task.s(xnat_credentials=self.auth, file_path=file_path)

        get_uris_signature = get_uris.s(xnat_credentials=self.auth)

        return create_resources_signature | upload_signature | get_uris_signature

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
                error = e
                # print to a log file
            return e

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






