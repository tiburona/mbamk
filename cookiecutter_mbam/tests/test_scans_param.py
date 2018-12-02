import pytest
import os
from pytest_mock import mocker
from datetime import datetime
from werkzeug.datastructures import FileStorage
from cookiecutter_mbam.user import User
from cookiecutter_mbam.scan import Scan
from cookiecutter_mbam.experiment import Experiment
from cookiecutter_mbam.experiment.service import ExperimentService
from cookiecutter_mbam.scan.service import ScanService, gzip_file
from unittest.mock import patch
from shutil import copy
from .factories import UserFactory
from .factories import ExperimentFactory
from factory import Iterator, Sequence, PostGenerationMethodCall
import faker
fake = faker.Faker()


def generate_parameters(num_exp, num_scans):
    test_data = []
    root_path  = '/data/archive/experiments/'
    for i in range(1,num_exp+1):
        for j in range(num_scans):
            exp_id = '000001_MR' + str(num_exp)
            scan_id = 'T1_' + str(num_scans + 1)
            exp_uri = os.path.join(root_path, exp_id)
            scan_uri = os.path.join(root_path, exp_id, 'scans', scan_id)
            test_data.append((num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri))
    return test_data


parameters = generate_parameters(2, 2)

@pytest.fixture(scope='function')
@pytest.mark.usefixtures('db')
def mocked_scan_service(db, mocker, request):
    user = User.create(email='a@b.com', username='hello', password='myprecious')
    num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = request.param

    for i in range(num_exp):
        #experiment = ExperimentFactory(user_id = user.id)
        date = fake.date_this_decade(before_today=True, after_today=False)
        scanner = 'GE'
        experiment = Experiment.create(user_id = user.id, date=date, scanner=scanner)
        db.session.add(experiment)

    ss = ScanService(experiment.user_id, experiment.id)
    for i in range(num_scans):
        ss._add_scan_to_database() # should this just be adding a scan via the same method as the experiments are added??

    ss.xc.upload_scan = mocker.MagicMock()
    ss.xc.upload_scan.return_value = ('/data/archive/subjects/000001',
                                      exp_uri,
                                      scan_uri)
    mocker.spy(ss, '_generate_xnat_identifiers')
    ss.param = request.param
    return ss

@pytest.mark.parametrize('mocked_scan_service', parameters, indirect=True)
@pytest.mark.parametrize('filename', ['T1.nii.gz', 'structural.nii', 'DICOMS.zip'])
class TestScanUpload:

    def copy_file_to_upload_dest(self, instance_path, basename):
        src_path = os.path.join(instance_path, 'files', basename)
        dst_path = os.path.join(instance_path, 'files', 'test_files')
        copy(src_path, dst_path)
        return os.path.join(dst_path, basename)

    def create_file_to_upload(self, scan_service, filename):
        path = self.copy_file_to_upload_dest(scan_service.instance_path, filename)
        return open(path, 'rb')

    def add_a_scan(self, scan_service, filename):
        with self.create_file_to_upload(scan_service, filename) as f:
            file = FileStorage(f)
            scan_service.add(file)
            file.close()
        return scan_service

    def setup_tests(self, scan_service, filename):
        scan_service = self.add_a_scan(scan_service, filename)
        retrieved_scans = Scan.query.filter((Scan.experiment_id == scan_service.experiment.id))
        scan = retrieved_scans.order_by(Scan.created_at.desc()).first()
        return (scan_service, retrieved_scans, scan)

    def test_before_file_upload_an_experiment_has_no_xnat_attributes(self, mocked_scan_service, filename):
        assert mocked_scan_service.experiment.xnat_uri == None
        assert mocked_scan_service.experiment.xnat_experiment_id == None

    def test_after_file_upload_experiment_has_the_right_number_of_scans(self, mocked_scan_service, filename):
        num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = mocked_scan_service.param
        scan_service, retrieved_scans, _ = self.setup_tests(mocked_scan_service, filename)
        assert retrieved_scans.count() == num_scans + 1
        assert scan_service.experiment.num_scans == num_scans + 1

    def test_after_file_upload_experiment_attributes_are_set(self, mocked_scan_service, filename):
        num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = mocked_scan_service.param
        scan_service, retrieved_scans, scan = self.setup_tests(mocked_scan_service, filename)
        assert scan_service.experiment.xnat_uri == exp_uri
        assert scan_service.experiment.xnat_experiment_id == exp_id

    def test_after_file_upload_scan_attributes_are_set(self, mocked_scan_service, filename):
        num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = mocked_scan_service.param
        scan_service, retrieved_scans, scan = self.setup_tests(mocked_scan_service, filename)
        assert scan.xnat_scan_id == scan_id
        assert scan.xnat_uri == scan_uri


