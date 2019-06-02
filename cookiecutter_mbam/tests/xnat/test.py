

import os
import responses
import configparser
import pytest
from cookiecutter_mbam.xnat.tasks import launch_command, dl_file_from_xnat


class TestXNATTasks:

    @property
    def file_depot(self):
        config = configparser.ConfigParser()
        config.read('../setup.cfg')
        return config['files']['file_depot']

    def generate_xnat_info(self):
        project = 'MBAM_TEST'
        config = configparser.ConfigParser()
        config.read('../setup.cfg')
        xnat_config = config['XNAT']
        server = xnat_config['server']
        xnat_credentials = (server, xnat_config['user'], xnat_config['password'])
        command_ids = (xnat_config['dicom_to_nifti_command_id'], xnat_config['dicom_to_nifti_wrapper_id'])
        command_id, wrapper_id = command_ids
        return project, server, xnat_credentials, command_ids, command_id, wrapper_id

    @responses.activate
    def test_dl_file_from_xnat(self):
        project, server, xnat_credentials, command_ids, command_id, wrapper_id = self.generate_xnat_info()

        scan_uri = '/data/experiments/XNAT_E00001/scans/10'
        files_uri = os.path.join(scan_uri, 'resources', 'NIFTI', 'files')
        file_uri = os.path.join(files_uri, 'T1.nii.gz')
        name = 'T1.nii.gz'
        test_file_src = '../test_files/T1.nii.gz'

        responses.add(responses.GET, server+ files_uri, status=200,
                      json={'ResultSet': {'Result': [{'Name': name, 'URI': file_uri}]}})

        with open(test_file_src, 'rb') as f:

            responses.add(responses.GET, server + file_uri, body=f.read(), status=200)
            task = dl_file_from_xnat.s(scan_uri, xnat_credentials, self.file_depot).apply()

            dl_path = os.path.join(self.file_depot, name)

            assert len(responses.calls) == 2
            assert task.result == name
            assert os.path.exists(dl_path)

        os.remove(dl_path)

    @responses.activate
    def test_dl_file_from_xnat_raises_value_error_if_failure_response(self):
        project, server, xnat_credentials, command_ids, command_id, wrapper_id = self.generate_xnat_info()

        scan_uri = '/data/experiments/XNAT_E00001/scans/10'
        files_uri = os.path.join(scan_uri, 'resources', 'NIFTI', 'files')

        status_code = 404

        responses.add(responses.GET, server + files_uri, status=status_code, json={'error': 'not found'})

        with pytest.raises(ValueError) as e_info:
            task = dl_file_from_xnat.s(scan_uri, xnat_credentials, self.file_depot).apply()

    # todo: this should raise some errors if something's wrong with the response
    # and my test should test that
    #todo: what's the actual status code for a post?
    @responses.activate
    def test_launch_command(self):
        project, server, xnat_credentials, command_ids, command_id, wrapper_id = self.generate_xnat_info()

        responses.add(responses.POST, '{}/xapi/projects/{}/commands/{}/wrappers/{}/launch'.
                      format(server, project, command_id, wrapper_id), json={'container-id': 'hello'},
                      status=200)

        uris = ['/data/subjects/XNAT_S00001', '/data/experiments/XNAT_E00001', '/data/experiments/XNAT_E00001/scans/10']

        task = launch_command.s(uris, xnat_credentials, project, command_ids).apply()

        assert task.result == 'hello'


tst = TestXNATTasks()

tst.test_dl_file_from_xnat()

tst.test_dl_file_from_xnat_raises_value_error_if_failure_response()










