import os
import responses
import configparser
import pytest
from cookiecutter_mbam.xnat.tasks import *

class TestXNATTasks:

    def __init__(self):
        self.project = 'MBAM_TEST'
        config = configparser.ConfigParser()
        config.read('../setup.cfg')
        self.file_depot = config['files']['file_depot']
        xnat_config = config['XNAT']
        self.server = xnat_config['server']
        self.xnat_credentials = (self.server, xnat_config['user'], xnat_config['password'])
        self.command_ids = (xnat_config['dicom_to_nifti_command_id'], xnat_config['dicom_to_nifti_wrapper_id'])
        self.command_id, self.wrapper_id = self.command_ids
        self.scan_uri = '/data/experiments/XNAT_E00001/scans/10'
        self.uris = {
            'subject': '/data/subjects/XNAT_S00001',
            'experiment': '/data/experiments/XNAT_E00001',
            'scan': self.scan_uri
        }

    @responses.activate
    def failure_response(self, mocked_uri, signature, method='GET'):
        responses.add(getattr(responses, method), mocked_uri, status=403, json={'error': 'not found'})
        with pytest.raises(ValueError) as e_info:
            signature.apply(throw=True)

    @responses.activate
    def success_response(self, mocked_uri, json, signature, method='GET', status=200):
        responses.add(getattr(responses, method), mocked_uri, status=status, json=json)
        return signature.apply()


class TestImportScanToXnat(TestXNATTasks):
    def __init__(self):
        super().__init__()
        self.mocked_uri = self.server + '/data/services/import'
        local_path = os.path.join(self.file_depot, 'DICOMS.zip')
        self.files = {'file': ('DICOMS.zip', open(local_path, 'rb'), 'application/octet-stream')}
        self.mocked_json_response = {}
        self.signature = import_scan_to_xnat.s(self.uris, self.xnat_credentials, local_path)

    def test_import_scan_to_xnat(self):
        task = self.success_response(self.mocked_uri, self.mocked_json_response, self.signature, method='POST')
        assert task.result == self.uris

    def test_import_scan_to_xnat_raises_error_if_failure_response(self):
        self.failure_response(self.mocked_uri, self.signature, method='POST')


class TestGetLatestScanInfo(TestXNATTasks):
    def __init__(self):
        super().__init__()
        self.mocked_uri = self.server + self.uris['experiment'] + '/scans'
        self.mocked_json_response = {
            'ResultSet':{
                'Result':
                    [{'xnat_imagescandata_id':'2', 'ID': '10', 'URI': self.scan_uri},
                     {'xnat_imagescandata_id':'1', 'ID': 'T1_1', 'URI': '/data/experiments/XNAT_E00001/scans/T1_1'}
                     ]
            }
        }
        self.signature = get_latest_scan_info.s(self.uris, self.xnat_credentials)

    def test_get_latest_scan_info(self):
        task = self.success_response(self.mocked_uri, json=self.mocked_json_response, signature=self.signature)
        assert task.result == {'xnat_id': '10', 'xnat_uri': self.scan_uri}

    def test_get_latest_scan_info_raises_error_if_failure_response(self):
        self.failure_response(self.mocked_uri, self.signature)


class TestPollCS(TestXNATTasks):

    def __init__(self):
        super().__init__()
        self.container_id = 'hello'
        self.mocked_uri = self.server + '/xapi/containers/{}'.format(self.container_id)
        self.signature = poll_cs.s(self.container_id, self.xnat_credentials)
        self.mocked_json_response = {'status': 'Complete'}

    @responses.activate
    def test_poll_cs_result_is_value_for_status_key_on_json_response(self):
        task = self.success_response(self.mocked_uri, {'status': 'Complete'}, self.signature)
        assert task.result == 'Complete'

    def test_poll_cs_raises_error_if_failure_response(self):
        self.failure_response(self.mocked_uri, self.signature)


class TestDLFileFromXnat(TestXNATTasks):

    def __init__(self):
        super().__init__()
        self.files_uri = os.path.join(self.scan_uri, 'resources', 'NIFTI', 'files')
        self.file_uri = os.path.join(self.files_uri, 'T1.nii.gz')
        self.signature = dl_file_from_xnat.s(self.scan_uri, self.xnat_credentials, self.file_depot)
        self.name = 'T1.nii.gz'
        self.test_file_src = '../test_files/T1.nii.gz'
        self.files_mock_args = [responses.GET, self.server + self.files_uri]
        self.files_mock_kwargs = {'status': 200, 'json': {'ResultSet': {'Result': [{'Name': self.name, 'URI': self.file_uri}]}}}

    @responses.activate
    def test_dl_file_from_xnat(self):

        responses.add(*self.files_mock_args, **self.files_mock_kwargs)

        with open(self.test_file_src, 'rb') as f:

            responses.add(responses.GET, self.server + self.file_uri, body=f.read(), status=200)
            task = self.signature.apply()

            dl_path = os.path.join(self.file_depot, self.name)

            assert len(responses.calls) == 2
            assert task.result == self.name
            assert os.path.exists(dl_path)

        os.remove(dl_path)

    def test_dl_file_from_xnat_raises_value_error_if_failure_response_for_files(self):
        self.failure_response(self.server + self.files_uri, self.signature)

    @responses.activate
    def test_dl_file_from_xnat_raises_value_error_if_failure_response_for_file(self):
        responses.add(*self.files_mock_args, **self.files_mock_kwargs)
        responses.add(responses.GET, self.server + self.file_uri, status=404, json={'error': 'not found'})
        with pytest.raises(ValueError) as e_info:
            self.signature.apply(throw=True)


class TestLaunchCommand(TestXNATTasks):

    def __init__(self):
        super().__init__()
        self.launch_uri = '{}/xapi/projects/{}/commands/{}/wrappers/{}/launch'.format(
            self.server, self.project, self.command_id, self.wrapper_id)
        self.signature = launch_command.s(self.scan_uri, self.xnat_credentials, self.project, self.command_ids)

    @responses.activate
    def test_launch_command(self):
        task = self.success_response(self.launch_uri, {'container-id': 'hello'}, self.signature, method='POST')
        assert task.result == 'hello'

    @responses.activate
    def test_launch_command_raises_value_error_if_failure_response(self):
        self.failure_response(self.launch_uri, self.signature, method='POST')

tistx = TestImportScanToXnat()

tistx.test_import_scan_to_xnat()

tistx.test_import_scan_to_xnat_raises_error_if_failure_response()

tdffx = TestDLFileFromXnat()

tdffx.test_dl_file_from_xnat()

tdffx.test_dl_file_from_xnat_raises_value_error_if_failure_response_for_file()

tdffx.test_dl_file_from_xnat_raises_value_error_if_failure_response_for_files()

tgls = TestGetLatestScanInfo()

tgls.test_get_latest_scan_info()

tgls.test_get_latest_scan_info_raises_error_if_failure_response()










