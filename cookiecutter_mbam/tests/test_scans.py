import pytest
import os
from pytest_mock import mocker
from datetime import datetime
from werkzeug.datastructures import FileStorage
from cookiecutter_mbam.user import User
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.experiment.service import ExperimentService
from cookiecutter_mbam.scan.service import ScanService, gzip_file
from flask import current_app
from unittest.mock import patch
from shutil import copy
import configparser



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

class TestScanUpload:

    def test_uncompressed_scan(self, new_scan_service):
        """
        Given that an uncompressed nii file is passed to the scan service upload method
        When the upload method calls _process_file
        gzip_file is also called with the local path to the file
        _process_file returns a two-tuple: (the path gzip_file returned, False_
        """
        instance_path = new_scan_service.instance_path
        upload_dest = new_scan_service.upload_dest
        nii_path = os.path.join(instance_path, 'files', 'structural.nii')
        new_scan_service.upload_dest
        copy(nii_path, upload_dest)
        nii_path = os.path.join(upload_dest, os.path.basename(nii_path))
        f = open(nii_path, 'rb')
        file = FileStorage(f)
        with patch('cookiecutter_mbam.scan.service.gzip_file') as mocked_gzip:
            zipped_path = os.path.join(upload_dest, 'structural.nii.gz')
            mocked_gzip.return_value = (open(nii_path, 'rb'), zipped_path)
            file_path, import_service = new_scan_service._process_file(file)
            mocked_gzip.assert_called_with(os.path.join(upload_dest, os.path.basename(nii_path)))
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

    def test_zip_file(self, new_scan_service, mocker):
        """
        Given that an zip folder of dicoms is passed to the scan service upload method
        When the upload method calls _process_file
        1) _process_file returns a two tuple: (the file path, True)
        2) _generate_xnat_identifers returns a dict in which the 'resource' type is 'DICOM'
        3) xnat_put is called with expected args, including imp=True
        """
        instance_path = new_scan_service.instance_path
        upload_dest = new_scan_service.upload_dest
        zip_path = os.path.join(instance_path, 'files', 'DICOMS.zip')
        copy(zip_path, upload_dest)
        zip_path = os.path.join(upload_dest, os.path.basename(zip_path))
        f = open(zip_path, 'rb')
        file = FileStorage(f)
        file_path, import_service = new_scan_service._process_file(file)
        assert import_service
        # assert file_path == os.path.join(upload_dest, 'DICOMS.zip')
        config = configparser.ConfigParser()
        config.read(os.path.join(instance_path, 'setup.cfg'))
        xc = XNATConnection(config=config['XNAT'])
        xc._xnat_put = mocker.MagicMock()
        new_scan_service.xc = xc
        new_scan_service._update_database_objects = mocker.MagicMock()
        mocker.spy(new_scan_service.xc, '_xnat_put')
        mocker.spy(new_scan_service, '_generate_xnat_identifiers')

        f = open(zip_path, 'rb')
        file = FileStorage(f)

        new_scan_service.add(file)
        new_scan_service._generate_xnat_identifiers.assert_called_with(dcm=True)
        xnat_ids = new_scan_service._generate_xnat_identifiers(dcm=True)
        assert xnat_ids['resource']['xnat_id'] == 'DICOM'
        new_scan_service.xc._xnat_put.assert_called_with(file_path=file_path, imp=True, project= 'MBAM_TEST',
                                                                   subject='000001', experiment='000001_MR2')
        f.close(); file.close()

    def test_xnat_ids_correctly_generated_for_multiple_experiments_and_scans(self, new_scan_service):
        """
        Given a subject with more than one experiment, and an experiment with more than one scan
        When xnat ids are generated
        Then test that xnat_experiment_id and xnat_scan_id are as expected
        """

        xnat_ids = new_scan_service._generate_xnat_identifiers()
        assert xnat_ids['experiment']['xnat_id'] == '000001_MR2'
        assert xnat_ids['scan']['xnat_id'] == 'T1_2'