import responses

import pytest
import random
from datetime import datetime
from cookiecutter_mbam.xnat.tasks import *
from cookiecutter_mbam.config import Config

config_vars = ['file_depot', 'xnat_host', 'xnat_user', 'xnat_password', 'xnat_docker_host', 'xnat_project',
               'dicom_to_nifti_command', 'dicom_to_nifti_wrapper', 'freesurfer_recon_command',
               'freesurfer_recon_wrapper', 'fs_to_mesh_command', 'fs_to_mesh_wrapper']


class TestXNATTasks:

    @pytest.fixture(autouse=True)
    def setup_xnat_tests(self):
        for config_var in config_vars:
            setattr(self, config_var, getattr(Config, config_var.upper()))
        self.auth = (self.xnat_host, self.xnat_user, self.xnat_password)
        self.scan_uri = '/data/experiments/XNAT_E00001/scans/10'
        self.ids = {
            'subject': 'XNAT_S00001',
            'experiment': 'XNAT_E00001'
        }
        self.uris = {
            'subject': '/data/subjects/XNAT_S00001',
            'experiment': '/data/experiments/XNAT_E00001',
            'scan': self.scan_uri
        }

    @responses.activate
    def failure_response(self, mocked_uri, signature, method='GET'):
        responses.add(getattr(responses, method), mocked_uri, status=404, json={'error': 'not found'})
        with pytest.raises(ValueError) as e_info:
            signature.apply(throw=True)

    @responses.activate
    def success_response(self, mocked_uri, json, signature, method='GET', status=200, assertions=[], **kwargs):
        responses.add(getattr(responses, method), mocked_uri, status=status, json=json, **kwargs)
        task = signature.apply()
        req = responses.calls[0].request
        for assertion in assertions:
            assert assertion(req)
        return task


class TestCreateResources(TestXNATTasks):

    @pytest.fixture(autouse=True, params=range(4))
    def setup_tests(self, setup_xnat_tests, request):

        to_create = [
            ['subject', 'experiment'],
            ['scan', 'resource'],
            ['experiment', 'scan', 'resource'],
            ['subject', 'experiment', 'scan', 'resource']
        ]

        ind = request.param

        self.to_create = to_create[ind]

        self.responses = {level: self.ids[level] for level in self.to_create if level in ['subject', 'experiment']}

        prefix = self.xnat_host + '/data/archive/projects/MBAM_TEST'
        subject_url = prefix + '/subjects/000001'
        experiment_url = subject_url + '/experiments/000001_MR1'
        scan_url = experiment_url + '/scans/T1_1'
        resource_url = scan_url + '/resources/NIFTI'
        file_url = resource_url + '/files/T1.nii.gz'

        date = datetime.now()

        self.mocked_urls = {
            'subject': subject_url,
            'experiment': experiment_url + '?xnat:mrSessionData/date={}'.format(date.strftime('%m/%d/%Y')),
            'scan': scan_url + '?xsiType=xnat:mrScanData',
            'resource': resource_url,
            'file':file_url + '?xsi:type=xnat:mrScanData'
        }

        self.signature = create_resources.s(self.auth, self.to_create, self.mocked_urls)


    @responses.activate
    def test_create_resources(self):

        for key in self.mocked_urls:
            body = self.responses[key] if key in self.responses else None
            responses.add('PUT', self.mocked_urls[key], status=200, body=body)

        task = self.signature.apply()
        assert len(responses.calls) == len(self.to_create)
        assert task.result == self.responses

    @responses.activate
    def test_create_resources_raises_error_if_failure_response(self):
        failure = random.randint(0, len(self.to_create) - 1)
        for i, key in enumerate(self.mocked_urls.keys()):
            body = self.responses[key] if key in self.responses else None
            kw = {'status': 404, 'json': {'error': 'not found'}} if i == failure else {'status': 200, 'body': body}
            responses.add('PUT', self.mocked_urls[key], **kw)


class TestUploadsAndImports(TestXNATTasks):

    @pytest.fixture(
        autouse=True,
        params=[('T1.nii.gz', False, '/resources/NIFTI/files/T1.nii.gz', 'PUT'),
                ('DICOMS.zip', True, '/data/services/import', 'POST')]
    )
    def setup_tests(self, setup_xnat_tests, request):
        filename, imp, uri, method = request.param
        if filename == 'T1.nii.gz':
            uri = self.scan_uri + uri
        self.mocked_url = self.xnat_host + uri
        self.method = method
        dir_path = os.path.dirname(os.path.realpath(__file__))
        par_path = os.path.abspath(os.path.join(dir_path, os.pardir, os.pardir))
        local_path = os.path.join(par_path, 'test_files', filename)
        self.files =  {'file': (filename, open(local_path, 'rb'), 'application/octet-stream')}
        self.mocked_json_response = {}
        self.signature = upload_scan_to_xnat.s(self.auth, local_path, self.mocked_url, self.uris['experiment'], imp,
                                               delete=False)
        self.assertions = [self.assert_request_type, self.assert_request_size]

    def assert_request_type(self, req):
        return req.headers['Content-Type'][0:19] == 'multipart/form-data'

    def assert_request_size(self, req):
        return int(req.headers['Content-Length']) > 1000

    def test_scan_to_xnat(self):
        task = self.success_response(self.mocked_url, self.mocked_json_response, self.signature,
                              method=self.method, assertions=self.assertions)
        assert task.result == self.uris['experiment']

    def test_scan_to_xnat_raises_error_if_failure_response(self):
        self.failure_response(self.mocked_url, self.signature, method=self.method)


class TestGetLatestScanInfo(TestXNATTasks):

    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
        self.mocked_url = self.xnat_host + self.uris['experiment'] + '/scans'
        self.mocked_json_response = {
            'ResultSet':{
                'Result':
                    [{'xnat_imagescandata_id':'2', 'ID': '10', 'URI': self.scan_uri},
                     {'xnat_imagescandata_id':'1', 'ID': 'T1_1', 'URI': '/data/experiments/XNAT_E00001/scans/T1_1'}
                     ]
            }
        }
        self.signature = get_latest_scan_info.s(self.uris['experiment'], self.auth)

    def test_get_latest_scan_info(self):
        task = self.success_response(self.mocked_url, json=self.mocked_json_response, signature=self.signature)
        assert task.result == {'xnat_id': '10', 'xnat_uri': self.scan_uri}

    def test_get_latest_scan_info_raises_error_if_failure_response(self):
        self.failure_response(self.mocked_url, self.signature)

# (self, uri, xnat_credentials, download_suffix, upload_suffix)


class TestGenContainerData(TestXNATTasks):

    @pytest.fixture(
        autouse=True,
        params=[('/resources/DICOM/files', '/resources/NIFTI/files')]
    )
    def setup_tests(self, setup_xnat_tests, request):
        self.download_suffix, self.upload_suffix = request.param
        self.signature = gen_container_data.s(self.scan_uri, self.auth, self.download_suffix, self.upload_suffix)

    def test_gen_container_data(self):
        task = self.signature.apply()
        assert task.result == {
            'download-url': self.xnat_host + self.scan_uri + self.download_suffix,
            'upload-url': self.xnat_host + self.scan_uri + self.upload_suffix,
            'xnat-host': self.xnat_host
    }


class TestLaunchCommand(TestXNATTasks):

    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
        self.command_ids = (self.dicom_to_nifti_command, self.dicom_to_nifti_wrapper)
        self.mocked_uri = '{}/xapi/projects/{}/commands/{}/wrappers/{}/launch'.format(
            self.xnat_host, self.xnat_project, self.dicom_to_nifti_command, self.dicom_to_nifti_wrapper)
        self.signature = launch_command.s(self.scan_uri, self.auth, self.xnat_project, self.command_ids)
        self.mocked_json_response = {'container-id': 'hello', 'id': 'hi'}

    def test_launch_command(self):
        task = self.success_response(self.mocked_uri, self.mocked_json_response, self.signature, method='POST')

        print("HEEELO", task.result)
        assert task.result == {'cs_id': 'hi', 'xnat_container_id': 'hello', 'xnat_host': 'https://mind-xnat.nyspi.org'}

    def test_launch_command_raises_value_error_if_failure_response(self):
        self.failure_response(self.mocked_uri, self.signature, method='POST')


class TestPollCS(TestXNATTasks):
    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
        self.container_id = 'hello'
        self.container_info = {'xnat_container_id': self.container_id}
        self.mocked_uri = self.xnat_host + '/xapi/containers/{}'.format(self.container_id)
        self.signature = poll_cs_dcm2nii.s(self.container_info, self.auth, 1)
        self.mocked_json_response = {'status': 'Complete'}

    def test_poll_cs_dcm2nii_result_is_value_for_status_key_on_json_response(self):
        task = self.success_response(self.mocked_uri, json=self.mocked_json_response, signature=self.signature)
        assert task.result == 'Complete'

    def test_poll_cs_raises_error_if_failure_response(self):
        self.failure_response(self.mocked_uri, self.signature)



class TestDLFilesFromXnat(TestXNATTasks):

    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
        self.files_uri = os.path.join(self.scan_uri, 'resources', 'NIFTI', 'files')
        self.suffix = os.path.join('/resources', 'NIFTI', 'files')
        self.file_uri = os.path.join(self.files_uri, 'T1.nii.gz')
        self.signature = dl_files_from_xnat.s(self.scan_uri, self.auth, self.file_depot, suffix=self.suffix)
        self.name = 'T1.nii.gz'
        dir_path = os.path.dirname(os.path.realpath(__file__))
        par_path = os.path.abspath(os.path.join(dir_path, os.pardir, os.pardir))
        self.test_file_src = os.path.join(par_path, 'test_files', self.name)
        self.files_mock_args = [responses.GET, self.xnat_host + self.files_uri]
        self.files_mock_kwargs = {'status': 200,
                                  'json': {'ResultSet': {'Result': [{'Name': self.name, 'URI': self.file_uri}]}}}

    @responses.activate
    def test_dl_files_from_xnat(self):

        responses.add(*self.files_mock_args, **self.files_mock_kwargs)

        with open(self.test_file_src, 'rb') as f:

            responses.add(responses.GET, self.xnat_host + self.file_uri, body=f.read(), status=200)
            task = self.signature.apply()


            dl_path = os.path.join(self.file_depot, self.name)
            print("XYZ dlpath", dl_path)
            print("ABCD tst_file_src ", self.test_file_src)

            assert len(responses.calls) == 2
            assert task.result == self.name
            assert os.path.exists(dl_path)

        os.remove(dl_path)

    def test_dl_files_from_xnat_raises_value_error_if_failure_response_for_files(self):
        self.failure_response(self.xnat_host + self.files_uri, self.signature)

    @responses.activate
    def test_dl_files_from_xnat_raises_value_error_if_failure_response_for_file(self):
        responses.add(*self.files_mock_args, **self.files_mock_kwargs)
        responses.add(responses.GET, self.xnat_host + self.file_uri, status=404, json={'error': 'not found'})
        with pytest.raises(ValueError) as e_info:
            self.signature.apply(throw=True)
