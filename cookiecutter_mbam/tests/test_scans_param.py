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


def generate_parameters():
    test_data = []
    root_path  = '/data/archive/experiments/'
    for num_exp in range(1,3):
        for num_scans in range(2):
            exp_id = '000001_MR' + str(num_exp )
            scan_id = 'T1_' + str(num_scans + 1)
            exp_uri = os.path.join(root_path, exp_id)
            scan_uri = os.path.join(root_path, exp_id, 'scans', scan_id)
            test_data.append((num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri))
    return test_data


parameters = generate_parameters()

@pytest.fixture(scope='function')
@pytest.mark.usefixtures('db')
def mocked_scan_service(db, mocker, request):
    user = User.create(email='a@b.com', username='hello', password='myprecious')

    for num_exp in range(request.param[0]):
        #experiment = ExperimentFactory(user_id = user.id)
        date = fake.date_this_decade(before_today=True, after_today=False)
        scanner = 'GE'
        experiment = Experiment.create(user_id = user.id, date=date, scanner=scanner)
        db.session.add(experiment)

    ss = ScanService(experiment.user_id, experiment.id)
    for num_scan in range(request.param[1]):
        ss._add_scan_to_database() # should this just be adding a scan via the same method as the experiments are added??

    ss.xc.upload_scan = mocker.MagicMock()
    ss.xc.upload_scan.return_value = ('/data/archive/subjects/000001',
                                      request.param[4],
                                      request.param[5])
    mocker.spy(ss, '_generate_xnat_identifiers')
    ss.param = request.param
    return ss


class TestScanUpload:

    def copy_file_to_upload_dest(self, scan_service, basename):
        instance_path = scan_service.instance_path
        src_path = os.path.join(instance_path, 'files', basename)
        dst_path = os.path.join(instance_path, 'files', 'test_files')
        copy(src_path, dst_path)
        return os.path.join(dst_path, basename)

    @pytest.mark.parametrize('mocked_scan_service', parameters, indirect=True)
    @pytest.mark.parametrize('filename', ['T1.nii.gz', 'structural.nii', 'DICOMS.zip'])
    def test_add(self, mocked_scan_service, filename):
        num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = mocked_scan_service.param
        path = self.copy_file_to_upload_dest(mocked_scan_service, filename)
        f = open(path, 'rb')
        file = FileStorage(f)
        experiment = mocked_scan_service.experiment
        assert experiment.xnat_uri == None
        assert experiment.xnat_experiment_id == None
        mocked_scan_service.add(file)
        retrieved_scans = Scan.query.filter((Scan.experiment_id == experiment.id))
        assert retrieved_scans.count() == num_scans + 1  # really should be the number of scans I added to the experiment
        assert mocked_scan_service.experiment.num_scans == num_scans + 1  # same as before
        scan = retrieved_scans.order_by(Scan.created_at.desc()).first()
        assert experiment.xnat_uri == exp_uri  # can retrieve from test_data
        assert experiment.xnat_experiment_id == exp_id
        assert scan.xnat_scan_id == scan_id
        assert scan.xnat_uri == scan_uri
        f.close()
