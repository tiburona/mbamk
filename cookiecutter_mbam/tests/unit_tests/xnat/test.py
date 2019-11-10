import os
import responses

import pytest
import collections
import random
from datetime import datetime
from cookiecutter_mbam.xnat.tasks import *
from cookiecutter_mbam.xnat.service import XNATConnection
from cookiecutter_mbam.config import config_by_name, config_name


class TestXNATTasks:
    @pytest.fixture(autouse=True)
    def setup_xnat_tests(self):
        self.project = 'MBAM_TEST'
        config = config_by_name[config_name]
        self.file_depot = config.files['file_depot']
        self.xnat_config = config.XNAT
        self.server = self.xnat_config['server']
        self.xnat_credentials = (self.server, self.xnat_config['user'], self.xnat_config['password'])
        self.command_ids = (self.xnat_config['dicom_to_nifti_command_id'], self.xnat_config['dicom_to_nifti_wrapper_id'])
        self.command_id, self.wrapper_id = self.command_ids
        self.scan_uri = '/data/experiments/XNAT_E00001/scans/10'
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

    @pytest.fixture(autouse=True, params=[True, False])
    def setup_tests(self, setup_xnat_tests, request):
        dcm = request.param

        User = collections.namedtuple('User', 'id num_experiments xnat_id')
        Experiment = collections.namedtuple('Experiment', 'id date num_scans xnat_id')

        user = User(id=1, num_experiments=1, xnat_id=None)
        date = datetime.now()
        experiment = Experiment(id=1, num_scans=0, date=date, xnat_id=None)

        xc = XNATConnection(self.xnat_config, set_docker_host=False)
        xc.generate_xnat_identifiers(user, experiment, dcm=dcm)

        levels = ['subject', 'experiment', 'scan', 'resource', 'file']

        self.signature = create_resources.s(self.xnat_credentials, (xc.xnat_ids, xc.existing_xnat_ids), levels, dcm,
                                            xc.archive_prefix)

        prefix = '/data/archive/projects/MBAM_TEST'
        subject_uri = prefix + '/subjects/000001'
        experiment_uri = subject_uri + '/experiments/000001_MR1'
        scan_uri = experiment_uri + '/scans/T1_1'
        resource_uri = scan_uri + '/resources/NIFTI'
        file_uri = resource_uri + '/files/T1.nii.gz'
        uris = [subject_uri, experiment_uri, scan_uri, resource_uri, file_uri]

        queries= ['', '?xnat:mrSessionData/date={}'.format(date.strftime('%m/%d/%Y')), '?xsiType=xnat:mrScanData', '',
                  '?xsi:type=xnat:mrScanData']

        if dcm:
            levels = levels[:-3]
            uris = uris[:-3]
            queries = queries[:-3]

        self.num_expected_calls = 2 if dcm else 5

        self.mocked_uris = zip(levels, uris, queries)

        self.uris = {level[0]:level[1] for level in zip(levels, uris, queries)}

    @responses.activate
    def test_create_resources(self):

        for _, uri, query in self.mocked_uris:
            responses.add('PUT', self.server + uri + query, status=200, json={})

        task = self.signature.apply()
        assert len(responses.calls) == self.num_expected_calls
        assert task.result == self.uris

    @responses.activate
    def test_get_latest_scan_info_raises_error_if_failure_response(self):
        failure = random.randint(0, self.num_expected_calls - 1)
        for i, (_, uri, query) in enumerate(self.mocked_uris):
            kw = {'status': 404, 'json':{'error': 'not found'}} if i is failure else {'status': 200, 'json':{}}
            responses.add('PUT', self.server + uri + query, **kw)

        with pytest.raises(ValueError):
            self.signature.apply(throw=True)


class TestUploadsAndImports(TestXNATTasks):

    @pytest.fixture(
        autouse=True,
        params=[('T1.nii.gz', upload_scan_to_xnat, '/resources/NIFTI/files/T1.nii.gz', 'PUT'),
                ('DICOMS.zip', import_scan_to_xnat, '/data/services/import', 'POST')]
    )
    def setup_tests(self, setup_xnat_tests, request):
        filename, celery_task, uri, method = request.param
        if filename == 'T1.nii.gz':
            uri = self.scan_uri + uri
            self.uris['resource'] = os.path.join(self.scan_uri, 'resources', 'NIFTI')
            self.uris['file'] = uri
        self.mocked_uri = self.server + uri
        self.method = method
        dir_path = os.path.dirname(os.path.realpath(__file__))
        par_path = os.path.abspath(os.path.join(dir_path, os.pardir, os.pardir))
        local_path = os.path.join(par_path, 'test_files', filename)
        self.files =  {'file': (filename, open(local_path, 'rb'), 'application/octet-stream')}
        self.mocked_json_response = {}
        self.signature = celery_task.s(self.uris, self.xnat_credentials, local_path)
        self.assertions = [self.assert_request_type, self.assert_request_size]

    def assert_request_type(self, req):
        return req.headers['Content-Type'][0:19] == 'multipart/form-data'

    def assert_request_size(self, req):
        return int(req.headers['Content-Length']) > 1000

    def test_scan_to_xnat(self):
        task = self.success_response(self.mocked_uri, self.mocked_json_response, self.signature,
                              method=self.method, assertions=self.assertions)
        assert task.result == self.uris

    def test_scan_to_xnat_raises_error_if_failure_response(self):
        self.failure_response(self.mocked_uri, self.signature, method=self.method)


class TestGetLatestScanInfo(TestXNATTasks):
    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
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


class TestGenDicomConversionData(TestXNATTasks):

    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
        self.signature = gen_dicom_conversion_data.s(self.scan_uri)

    def test_gen_dicom_conversion_data(self):
        task = self.signature.apply()
        assert task.result == {'scan': self.scan_uri[5:]}


class TestLaunchCommand(TestXNATTasks):

    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
        self.mocked_uri = '{}/xapi/projects/{}/commands/{}/wrappers/{}/launch'.format(
            self.server, self.project, self.command_id, self.wrapper_id)
        self.signature = launch_command.s(self.scan_uri, self.xnat_credentials, self.project, self.command_ids)
        self.mocked_json_response = {'container-id': 'hello'}

    def test_launch_command(self):
        task = self.success_response(self.mocked_uri, self.mocked_json_response, self.signature, method='POST')
        assert task.result == 'hello'

    def test_launch_command_raises_value_error_if_failure_response(self):
        self.failure_response(self.mocked_uri, self.signature, method='POST')


class TestPollCS(TestXNATTasks):
    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
        self.container_id = 'hello'
        self.mocked_uri = self.server + '/xapi/containers/{}'.format(self.container_id)
        self.signature = poll_cs.s(self.container_id, self.xnat_credentials)
        self.mocked_json_response = {'status': 'Complete'}

    def test_poll_cs_result_is_value_for_status_key_on_json_response(self):
        task = self.success_response(self.mocked_uri, json=self.mocked_json_response, signature=self.signature)
        assert task.result == 'Complete'

    def test_poll_cs_raises_error_if_failure_response(self):
        self.failure_response(self.mocked_uri, self.signature)


class TestDLFileFromXnat(TestXNATTasks):
    @pytest.fixture(autouse=True)
    def set_up(self, setup_xnat_tests):
        self.files_uri = os.path.join(self.scan_uri, 'resources', 'NIFTI', 'files')
        self.file_uri = os.path.join(self.files_uri, 'T1.nii.gz')
        self.signature = dl_file_from_xnat.s(self.scan_uri, self.xnat_credentials, self.file_depot)
        self.name = 'T1.nii.gz'
        dir_path = os.path.dirname(os.path.realpath(__file__))
        par_path = os.path.abspath(os.path.join(dir_path, os.pardir, os.pardir))
        self.test_file_src = os.path.join(par_path, 'test_files', self.name)
        self.files_mock_args = [responses.GET, self.server + self.files_uri]
        self.files_mock_kwargs = {'status': 200,
                                  'json': {'ResultSet': {'Result': [{'Name': self.name, 'URI': self.file_uri}]}}}

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





