import pytest
import os
from pytest_mock import mocker
from datetime import datetime
from werkzeug.datastructures import FileStorage
from cookiecutter_mbam.user import User
from cookiecutter_mbam.scan import Scan
from cookiecutter_mbam.experiment.service import ExperimentService
from cookiecutter_mbam.scan.service import ScanService, gzip_file
from unittest.mock import patch
from shutil import copy
from .factories import UserFactory
from .factories import ExperimentFactory
from factory import Iterator, Sequence, PostGenerationMethodCall
import faker
fake = faker.Faker()

# Todo: write functional test assessing whether XNAT upload works.  It should actually add a scan to XNAT
# then query XNAT to find out if the scan is there.
# Todo: write unit test of add method.  This should assess only that the database changes are as expected for all
# three types of scans
# would a feature test check how scan service and xnat service were working together?


# what if I parameterize only the fixture.  I accept that I need three tests for gz



def generate_parameters():
    test_data = []
    root_path  = '/data/archive/experiments/'
    for num_exp in range(2):
        for num_scans in range(2):
            exp_id = '000001_MR' + str(num_exp + 1)
            scan_id = 'T1_' + str(num_scans + 1)
            exp_uri = os.path.join(root_path, exp_id)
            scan_uri = os.path.join(root_path, exp_id, 'scans', scan_id)
            test_data.append((num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri))
    return test_data


parameters = generate_parameters()

@pytest.fixture(scope='function')
@pytest.mark.usefixtures('db')
def mocked_scan_service(db, mocker, request):
    user = UserFactory(password='myprecious')
    db.session.add(user)

    for num_exp in range(request.param[0]):
        experiment = ExperimentFactory(user_id = user.id)
        db.session.add(experiment)

    ss = ScanService(experiment.user_id, experiment.id)
    for num_scan in range(request.param[1]):
        ss._add_scan_to_database()

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
    def test_add(self, mocked_scan_service):
        for file_name in ['T1.nii.gz', 'structural.nii', 'DICOMS.zip']:
            path = self.copy_file_to_upload_dest(mocked_scan_service, file_name)
            f = open(path, 'rb')
            file = FileStorage(f)
            experiment = mocked_scan_service.experiment
            assert experiment.xnat_uri == None
            assert experiment.xnat_id == None
            mocked_scan_service.add(file)
            retrieved_scans = Scan.query.filter((Scan.experiment_id == mocked_scan_service.experiment.id))
            assert retrieved_scans.count() == parameters[1] # really should be the number of scans I added to the experiment
            assert mocked_scan_service.experiment.num_scans == parameters[1] # same as before
            scan = retrieved_scans.order_by(Scan.created_at.desc()).first()
            assert experiment.xnat_uri ==  mocked_scan_service.param[4]# can retrieve from test_data
            assert experiment.xnat_id == mocked_scan_service.param[2]
            assert scan.xnat_id == mocked_scan_service.param[3]
            assert scan.xnat_uri == mocked_scan_service.param[5]



    def test_gz_add(self, mocked_scan_service):
        gz_path = self.copy_file_to_upload_dest(mocked_scan_service, 'T1.nii.gz')
        f = open(gz_path, 'rb')
        file = FileStorage(f)
        experiment = mocked_scan_service.experiment
        assert experiment.xnat_uri == None
        assert experiment.xnat_id == None
        mocked_scan_service.add(file)
        retrieved_scans = Scan.query.filter((Scan.experiment_id == mocked_scan_service.experiment.id))
        assert retrieved_scans.count() == 2
        assert mocked_scan_service.experiment.num_scans == 2
        scan = retrieved_scans.order_by(Scan.created_at.desc()).first()
        assert experiment.xnat_uri == '/data/archive/experiments/000001_MR2'
        assert experiment.xnat_id == '000001_MR2'
        assert scan.xnat_id == 'T1_2'
        assert scan.xnat_uri == '/data/archive/experiments/000001_MR2/scans/T1_2'




    def test_gzip(self, new_scan_service):
        """
        When the gzip utility function is called with a path to a file
        It returns a gzipped file object and the path to that file on disk
        And the file name of the new gzipped file is the old file name + the .gz extension
        """
        nii_path = os.path.join(new_scan_service.instance_path, 'files', 'structural.nii')
        file_object, file_path = gzip_file(nii_path)
        assert type(file_object).__name__ == 'GzipFile'
        assert os.path.basename(file_path) == 'structural.nii.gz'
        os.remove(file_path)

    def test_process_zip_file(self, mocked_scan_service):
        """
        When _process_file is passed a zip file, it returns a two tuple: (the file path, True)
        """
        zip_path = self.copy_file_to_upload_dest(mocked_scan_service, 'DICOMS.zip')
        with open(zip_path, 'rb') as f:
            file = FileStorage(f)
            file_path, import_service = mocked_scan_service._process_file(file)
            assert import_service
            assert file_path == os.path.join(mocked_scan_service.upload_dest, 'DICOMS.zip')
            file.close()

    def test_zip_file_initiates_import_service(self, mocked_scan_service):
        """
        Given that a zip file is passed to the add method,
        when _generate_xnat_ids is called it generates a resource id of 'DICOM',
        and when _xnat_put is called it is passed arguments that will invoke the import service
        :param mocked_scan_service:
        :return:
        """
        # todo: I think this test is inappropriate, in that it reaches in to test a method on the xnat service
        # it would be more appropriate to test what xc.upload_scan was called with
        # as it stands it's creating coupling.  These are supposedly tests of scan service, but they break if I
        # change the xnat service
        zip_path = self.copy_file_to_upload_dest(mocked_scan_service, 'DICOMS.zip')
        upload_path = os.path.join(mocked_scan_service.instance_path, 'static', 'files', 'DICOMS.zip')
        with open(zip_path, 'rb') as f:
            file = FileStorage(f)
            mocked_scan_service.add(file)
            mocked_scan_service._generate_xnat_identifiers.assert_called_with(dcm=True)
            xnat_ids = mocked_scan_service._generate_xnat_identifiers(dcm=True)
            assert xnat_ids['resource']['xnat_id'] == 'DICOM'
            #mocked_scan_service.xc._xnat_put.assert_called_with(file_path=upload_path, imp=True, project='MBAM_TEST',
                                                            #subject='000001', experiment='000001_MR2')
            file.close()

    def test_xnat_ids_correctly_generated_for_multiple_experiments_and_scans(self, new_scan_service):
        """
        Given a subject with more than one experiment, and an experiment with more than one scan
        When xnat ids are generated
        Then test that xnat_experiment_id and xnat_scan_id are as expected
        """

        xnat_ids = new_scan_service._generate_xnat_identifiers()
        assert xnat_ids['experiment']['xnat_id'] == '000001_MR2'
        assert xnat_ids['scan']['xnat_id'] == 'T1_2'