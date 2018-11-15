import pytest
from pytest_mock import mocker
from datetime import datetime
from werkzeug.datastructures import FileStorage
from cookiecutter_mbam.user import User
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.experiment.service import ExperimentService
from cookiecutter_mbam.scan.service import ScanService


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('db')
def new_scan_service(db):
    user = User.create(username='Princess Leia', email='dontatme@me.com')
    date = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
    es = ExperimentService()
    es.add(date=date, scanner='GE', num_scans=2, user=user)
    experiment2 = es.add(date=date, scanner='GE', num_scans=2, user=user)
    ss1 = ScanService(user.id, experiment2.id)
    ss1._add_scan()
    ss2 = ScanService(user.id, experiment2.id)
    return ss2

class TestScanUpload:

    def test_uncompressed_scan(self, new_scan_service):
        """
        Given that an uncompressed nii file is passed to the scan service upload method
        When the upload method calls _process_file
        _process_file returns a two tuple: (the gzipped file object, False)
        """

        with open('/Users/katie/spiro/cookiecutter_mbam/files/T1.nii', 'rb') as f:
            file_object, import_service = new_scan_service._process_file(f)
            assert not import_service
            assert type(file_object).__name__ == 'GzipFile'

    def test_zip_file(self, new_scan_service, mocker):
        """
        Given that an zip folder of dicoms is passed to the scan service upload method
        When the upload method calls _process file
        1) _process_file returns a two tuple: (the file object, True)
        2) _generate_xnat_identifers returns a dict in which the 'resource' type is 'DICOM'
        3) xnat_put is called with expected args, including imp=True
        """

        with open('/Users/katie/spiro/cookiecutter_mbam/files/DICOM.zip', 'rb') as f:
            file = FileStorage(f)
            file.save('/Users/katie/spiro/cookiecutter_mbam/files/DICOM1.zip')
            print(type(file))
            print(file.filename)

        print("hey ", type(file))
        file_object, import_service = new_scan_service._process_file(file)
        assert import_service
        xc = XNATConnection()
        xc.xnat_put = mocker.MagicMock()
        mocker.spy(new_scan_service.xc, 'xnat_put')
        mocker.spy(new_scan_service, '_generate_xnat_identifiers')
        new_scan_service.upload(f)
        new_scan_service._generate_xnat_identifiers.assert_called_with(dcm=True)
        xnat_ids = new_scan_service._generate_xnat_identifiers(dcm=True)
        assert xnat_ids['resource']['xnat_id'] == 'DICOM'
        new_scan_service.xc.xnat_put.assert_called_with(file=f, imp=True, project= 'MBAM_TEST',
                                                                   subject='000001', experiment='000001_MR2')



    def test_xnat_ids_correctly_generated_for_multiple_experiments_and_scans(self, new_scan_service):
        """
        Given a subject with more than one experiment, and an experiment with more than one scan
        When xnat ids are generated
        Then test that xnat_experiment_id and xnat_scan_id are as expected
        """

        with open('/Users/katie/spiro/cookiecutter_mbam/files/T1.nii.gz', 'rb') as f:
            xnat_ids = new_scan_service._generate_xnat_identifiers()
            assert xnat_ids['experiment']['xnat_id'] == '000001_MR2'
            assert xnat_ids['scan']['xnat_id'] == 'T1_2'
