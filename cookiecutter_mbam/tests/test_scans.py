import pytest
import os
from pytest_mock import mocker
from datetime import datetime
from werkzeug.datastructures import FileStorage
from cookiecutter_mbam.user import User
from cookiecutter_mbam.experiment.service import ExperimentService
from cookiecutter_mbam.scan.service import ScanService, gzip_file
from unittest.mock import patch
from shutil import copy

# Todo: write functional test assessing whether XNAT upload works.  It should actually add a scan to XNAT
# then query XNAT to find out if the scan is there.
# Todo: write unit test of add method.  This should assess only that the database changes are as expected for all
# three types of scans



@pytest.fixture(scope='function')
@pytest.mark.usefixtures('db')
def new_scan_service(db):
    user = User.create(username='Princess Leia', email='dontatme@me.com')
    date = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
    es = ExperimentService()
    es.add(date=date, scanner='GE', num_scans=2, user=user)
    experiment2 = es.add(date=date, scanner='GE', num_scans=2, user=user)
    ss1 = ScanService(user.id, experiment2.id)
    ss1._add_scan_to_database()
    ss2 = ScanService(user.id, experiment2.id)
    return ss2

@pytest.fixture(scope='function')
@pytest.mark.usefixtures('db')
def mocked_scan_service(db, mocker):
    ss = new_scan_service(db)
    ss.xc._xnat_put = mocker.MagicMock()
    ss._update_database_objects = mocker.MagicMock()
    mocker.spy(ss.xc, '_xnat_put')
    mocker.spy(ss, '_generate_xnat_identifiers')
    return ss

# todo: find another place to copy files to so I actually test the copying process.

class TestScanUpload:

    def copy_file_to_upload_dest(self, scan_service, basename):
        instance_path = scan_service.instance_path
        src_path = os.path.join(instance_path, 'files', basename)
        dst_path = os.path.join(instance_path, 'files', 'test_files')
        copy(src_path, dst_path)
        return os.path.join(dst_path, basename)

    def test_process_uncompressed_scan(self, new_scan_service):
        """
        Given that an uncompressed nii file is passed to the scan service upload method
        When the upload method calls _process_file
        gzip_file is also called with the local path to the file
        _process_file returns a two-tuple: (the path gzip_file returned, False)
        """
        nii_path = self.copy_file_to_upload_dest(new_scan_service, 'structural.nii')
        f = open(nii_path, 'rb')
        file = FileStorage(f)
        with patch('cookiecutter_mbam.scan.service.gzip_file') as mocked_gzip:
            zipped_path = os.path.join(new_scan_service.upload_dest, 'structural.nii.gz')
            mocked_gzip.return_value = (open(nii_path, 'rb'), zipped_path)
            file_path, import_service = new_scan_service._process_file(file)
            mocked_gzip.assert_called_with(os.path.join(new_scan_service.upload_dest, os.path.basename(nii_path)))
            assert not import_service


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
            mocked_scan_service.xc._xnat_put.assert_called_with(file_path=upload_path, imp=True, project='MBAM_TEST',
                                                            subject='000001', experiment='000001_MR2')
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