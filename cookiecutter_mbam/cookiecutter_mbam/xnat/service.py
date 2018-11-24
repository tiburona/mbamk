import os
import xnat
import configparser

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class XNATConnection:

    def __init__(self, config):
        self.xnat_config = config
        self._set_attributes()
        self.xnat_hierarchy = ['subject', 'experiment', 'scan', 'resource', 'file']

    def _read_config(self):
        """ Read config file

        Part of the instance initialization, reads config file for XNAT variables and uploaded file destination

        :return: None
        """
        config = configparser.ConfigParser()
        config_path = os.path.join(current_app.instance_path[:-8], 'setup.cfg')
        config.read(config_path)
        self.xnat_config = config['XNAT']
        self.upload_config = config['uploads']

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
    def xnat_put(self, url='', file_path=None, imp=False, **kwargs):
        """ The method to create an XNAT object

        Uses the xnatpy session.put, session.upload, or session.services.import_ method to add an object to XNAT.

        :param str url: a put route in the XNAT API
        :param str file_path: path to a file to upload
        :param bool imp: whether to use the import service (True if file is zip of dicoms, otherwise False)
        :param kwargs kwargs: arguments to pass to the import service (project, subject, and experiment)
        :return: None
        """
        with xnat.connect(self.server, self.user, self.password) as session:
            if imp:
                session.services.import_(file_path, overwrite='delete', **kwargs)
                    # todo: need to call something like xnat_get to get the scan uri and return it to calling method
            elif file_path:
                session.upload(url, file_path)
            else:
                try:
                    session.put(url)
                except:
                    pass

    def xnat_get(self):
        # todo: This needs to be a method that gets the name of the scan uri some how.
        pass

    def xnat_delete(self, url):
        # this needs to delete the specified resource from xNAT
        try:
            with xnat.connect(self.server, self.user, self.password) as session:
                session.delete(url)
        except:
            # todo: handle errors!
            pass

    # todo: fix the fake scan uri
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
            except: #todo specify KeyError here?
                query = ''

            if level == 'file':
                self.xnat_put(url=uri + query, file_path=file_path)
            else:
                if not exists_already: self.xnat_put(url=uri + query)

        if import_service:
            self.xnat_put(file_path=file_path, imp=True, project=self.project,
                          subject = self.xnat_ids['subject']['xnat_id'],
                          experiment = self.xnat_ids['experiment']['xnat_id'])

        # todo: make this the real scan uri!
        try:
            uris['scan']
        except:
            uris['scan'] = 'hello'

        return (uris['subject'], uris['experiment'], uris['scan'])
