import os
import responses
import configparser
import pytest
from cookiecutter_mbam import celery
from cookiecutter_mbam.utils.request_utils import init_session


@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def get_latest_scan_info(self, uris, xnat_credentials):
    server, user, password = xnat_credentials
    with init_session(user, password) as s:
        r = s.get(server + uris['experiment'] + '/scans')
        if r.ok:
            scans = r.json()['ResultSet']['Result']
            scans = sorted(scans, key=lambda scan: int(scan['xnat_imagescandata_id']))
            scan_uri = scans[-1]['URI']
            scan_id = scans[-1]['ID']
            return {'xnat_id': scan_id, 'xnat_uri': scan_uri}
        else:
            raise ValueError(f'Unexpected status code: {r.status_code}')

class TestXNATTasks:

    def assign_vars(self):
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


class TestGetLatestScanInfo(TestXNATTasks):
    def assign_vars(self):
        super().assign_vars()
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

    def test_get_latest_scan_info_success(self):
        self.assign_vars()
        task = self.success_response(self.mocked_uri, json=self.mocked_json_response, signature=self.signature)
        assert task.result == {'xnat_id': '10', 'xnat_uri': self.scan_uri}

    def test_get_latest_scan_info_raises_error_if_failure_response(self):
        self.assign_vars()
        self.failure_response(self.mocked_uri, self.signature)



#
# tgls = TestGetLatestScanInfo()
#
# tgls.test_get_latest_scan_info()
#
# tgls.test_get_latest_scan_info_raises_error_if_failure_response()










