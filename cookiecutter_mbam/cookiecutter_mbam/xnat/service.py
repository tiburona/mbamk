import os
import xnat
import configparser

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class XNATConnection:

    def __init__(self):
        self._read_config()
        self._set_attributes()
        self.xnat_hierarchy = ['subject', 'experiment', 'scan', 'resource', 'file']

    def _read_config(self):
        """ Read config file

        Part of the instance initialization, reads config file for XNAT variables and uploaded file destination

        :return: None
        """
        config = configparser.ConfigParser()
        config.read('/Users/katie/spiro/cookiecutter_mbam/setup.cfg')
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
            self.file_dest = self.upload_config['uploaded_scans_dest']

    def xnat_put(self, url='', file=None, imp=False, **kwargs):
        """ The method to create an XNAT object

        Uses the xnatpy session.put, session.upload, or session.services.import_ to add an object to XNAT.

        :param str url: a put route in the XNAT URI
        :param file object file: a file object to upload
        :param bool imp: whether to use the import service (True if file is zip of dicoms, otherwise False)
        :param kwargs kwargs:
        :return: None
        """
        with xnat.connect(self.server, self.user, self.password) as session:
            try:
                if imp:
                    file_path = os.path.join(self.file_dest, file.filename)
                    file.save(file_path)
                    session.services.import_(file_path, overwrite='delete', **kwargs)
                    os.remove(file_path)
                    # todo: need to call something like xnat_get to get the scan uri and return it to calling method
                elif file:
                    session.upload(url, file)
                else:
                    session.put(url)
            except:
                # todo
                # what should we do with errors?
                # probably depends on what the error is.  if we don't succeed in uploading the file
                # we need to send a message back to the user
                # but some errors here could be recoverable.

                pass

    def xnat_get(self):
        # todo: This needs to be a method that gets the name of the scan uri some how.
        pass

    # todo: fix the fake scan uri
    def upload_scan(self, xnat_ids, existing_xnat_ids, image_file, import_service=False):
        """The method to upload a scan to XNAT

        Iteratively constructs the uris for subject and experiment (if they do not exist).  Constructs the uris for scan,
        resource, and file (if not using the import service).  Calls xnat_put on the generated uris to create objects if
        they do not exist.  Calls xnat_put with a file to upload it, invoking the import service if it is a zip file.
        Returns uris for subject, experiment, and scan so they can be attached to their database objects.

        :param dict xnat_ids: a dictionary of xnat identifiers and query strings for put urls
        :param dict existing_xnat_ids: a dictionary of XNAT identifiers that already existed on user and experiment
        :param file object image_file: the scan file to upload
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
                self.xnat_put(url=uri + query, file=image_file)
            else:
                if not exists_already: self.xnat_put(url=uri + query)

        if import_service:
            self.xnat_put(file=image_file, imp=True, project=self.project,
                          subject = self.xnat_ids['subject']['xnat_id'],
                          experiment = self.xnat_ids['experiment']['xnat_id'])

        # todo: make this the real scan uri!
        try:
            uris['scan']
        except:
            uris['scan'] = 'hello'

        return (uris['subject'], uris['experiment'], uris['scan'])











