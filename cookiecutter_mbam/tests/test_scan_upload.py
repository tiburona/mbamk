
import pytest
import os
import json
import mock
from shutil import copy
from pytest_mock import mocker
from werkzeug.datastructures import FileStorage
from cookiecutter_mbam.scan import Scan
from cookiecutter_mbam.scan.service import ScanService, gzip_file, crop
from cookiecutter_mbam.derivation.service import Derivation, DerivationService
from .factories import UserFactory
from .factories import ExperimentFactory

# todo: why aren't my files being deleted from static/files.  add a test to make sure they are?


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('db', 'app')
def derivation_service(db, app):
    def _derivation_service(derivation_id, scan_id, config_dir = ''):
        ds = DerivationService(derivation_id, scan_id, config_dir)
        ds.xc.launch_command = mock.MagicMock()
        ds.xc.launch_command.return_value = {}
        print("I EXECUTED")
    return _derivation_service



@pytest.fixture(scope='function')
@pytest.mark.usefixtures('db', 'app')
def scan_service(db, app, request, mocker):
    """ Fixture to produce a ScanService object

      Returns a function that will return an instance of ScanService, optionally with some mocks (of the xnat_connection
      attribute) and spies (on the _generate_xnat_identifiers method). The returned scan service object also has a param
      attribute not found on a real scan service object -- this is so the parameters that are used to parametrize the
      fixture are also available inside the test.

      :param db: the database fixture
      :param app: the app fixture
      :param mocker: pytest object with mocking methods
      :param request: object that includes param attribute with test parameters
      :return: function that takes a boolean, mock.  If True, this function returns a mocked scan service object. Else,
      this function returns a scan service object with no attributes mocked.
      :rtype: function
      """
    num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = request.param

    user = UserFactory(password='myprecious')

    for i in range(num_exp):
        experiment = ExperimentFactory(user_id=user.id, user=user)
        db.session.add(experiment)
    db.session.commit()

    def _scan_service(do_mock):

        config_dir = os.path.join(app.instance_path[:-8], 'tests')

        ss = ScanService(experiment.user.id, experiment.id, config_dir=config_dir)

        for i in range(num_scans):
            ss._add_scan_to_database()

        ss.param = request.param

        if do_mock:
            ss.xc.upload_scan = mocker.MagicMock()
            ss.xc.upload_scan.return_value = ('/data/archive/subjects/000001', exp_uri, scan_uri)
            mocker.spy(ss, '_generate_xnat_identifiers')

        return ss

    return _scan_service

class ScanUploadSetup:
    """A collection of setup methods relevant to multiple scan upload test classes"""

    def copy_file_to_upload_dest(self, instance_path, filename):
        """Copy file to upload

        Copies a file to a staging location for testing (because local files are deleted after uploading)

        :param instance_path: the instance path attribute on the scan service
        :param filename: the name of the file to upload
        :return: the path to the file which will be opened and uploaded
        """
        src_path = os.path.join(instance_path, 'files', filename)
        dst_path = os.path.join(instance_path, 'files', 'test_files')
        copy(src_path, dst_path)
        return os.path.join(dst_path, filename)

    def create_file_to_upload(self, scan_service, filename):
        """Create file to upload

        :param scan_service: a ScanService object
        :param filename: the name of the file to upload
        :return: file object
        """
        path = self.copy_file_to_upload_dest(scan_service.instance_path, filename)
        return open(path, 'rb')

    def add_a_scan(self, scan_service, filename):
        """ Adds a scan via the scan service's add method
        :param scan_service: a mocked ScanService object
        :param filename: the name of the file to upload (from parameters)
        :return: a mocked ScanService object
        """
        with self.create_file_to_upload(scan_service, filename) as f:
            file = FileStorage(f)
            scan_service.add(file)
            file.close()
        return scan_service

    def open_file_storage_obj(self, scan_service, filename):
        """ Creates a FileStorage object
        :param scan_service: a ScanService object
        :param filename: the name of the file to upload
        :return: a two-tuple of a mocked ScanService object and the Werkzeug FileStorage object
        :rtype: tuple
        """
        f = self.create_file_to_upload(scan_service, filename)
        file = FileStorage(f)
        return (scan_service, file)

    def setup_tests(self, scan_service, filename, do_mock=True):
        """
        Kicks off creation of the ScanService object and scan upload
        :param scan_service: a ScanService object
        :param filename: the name of the file to upload
        :param mock: if True, mock some attributes of the ScanService object.  If False, don't.
        :return: a three-tuple of the ScanService object, all the scans for the current experiment, and the most
        recently created scan
        """
        scan_service = scan_service(do_mock=do_mock)
        scan_service = self.add_a_scan(scan_service, filename)
        retrieved_scans = Scan.query.filter((Scan.experiment_id == scan_service.experiment.id))
        scan = retrieved_scans.order_by(Scan.created_at.desc()).first()
        return (scan_service, retrieved_scans, scan)


# TODO: until I can make it so name of scan changes, change this to reflect real dicom uri
# or investigate whether I can make name of scan change
def generate_upload_test_parameters(range_exp, range_scans):
    """ Function to generate upload test parameters

    :param num_exp: the top end of the range of number of experiments
    :param num_scans: the top end of the range of number of scans
    :return: a list of tuples, one tuple for each time the parametrized test will be executed

        >>> generate_upload_test_parameters(1, 1)
        [(1, 0, '000001_MR1', 'T1_1', '/data/archive/experiments/000001_MR1',
        '/data/archive/experiments/000001_MR1/scans/T1_1')]
    """
    test_data = []
    root_path = '/data/archive/experiments/'
    for i in range(1, range_exp + 1):
        for j in range(range_scans):
            exp_id = '000001_MR' + str(i)
            scan_id = 'T1_' + str(j + 1)
            exp_uri = os.path.join(root_path, exp_id)
            scan_uri = os.path.join(root_path, exp_id, 'scans', scan_id)
            test_data.append((i, j, exp_id, scan_id, exp_uri, scan_uri))
    return test_data

# Each set of parameters is a list of tuples. The parameters in the tuple are number of scans, number of experiments,
# experiment id, scan id, experiment uri, and scan uri.  In the case where generate_upload_test_params is called with
# 2, 2, the set of parameters is a list of four tuples -- the set of parameters that result from the cross of all levels
# of the factors range_exp (the number of experiments) and range_scans (the number of scans)
large_set_of_params = generate_upload_test_parameters(2, 2)
small_set_of_params = generate_upload_test_parameters(1, 1)

@pytest.mark.parametrize('scan_service', large_set_of_params, indirect=True)
@pytest.mark.parametrize('filename', ['T1.nii.gz', 'structural.nii', 'DICOMS.zip'])
@mock.patch('cookiecutter_mbam.scan.service.DerivationService')
class TestScanUpload(ScanUploadSetup):
    """A class to test the public add method

    When parametrized with the three file types and a 2x2 matrix of number of scans x number of experiments,
    produces 12 parameter sets per test.  With each of those sets, tests: that before file upload and experiment has no
    XNAT attributes, that after file upload an experiment has added a scan, that after file upload xnat_experiment_id
    and xnat_uri are attributes of experiment, and that after file upload xnat_scan_id and xnat_uri are attributes of
    scan.
    """

    def test_before_file_upload_an_experiment_has_no_xnat_attributes(self, mock_DS, scan_service, filename):
        scan_service = scan_service(do_mock=True)
        assert scan_service.experiment.xnat_uri == None
        assert scan_service.experiment.xnat_experiment_id == None

    def test_after_file_upload_experiment_has_one_more_scan(self, mock_DS, scan_service, filename):
        scan_service, retrieved_scans, scan = self.setup_tests(scan_service, filename)
        num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = scan_service.param
        assert retrieved_scans.count() == num_scans + 1
        assert scan_service.experiment.num_scans == num_scans + 1

    def test_after_file_upload_experiment_attributes_are_set(self, mock_DS, scan_service, filename):
        scan_service, retrieved_scans, scan = self.setup_tests(scan_service, filename)
        num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = scan_service.param
        assert scan_service.experiment.xnat_uri == exp_uri
        assert scan_service.experiment.xnat_experiment_id == exp_id

    def test_after_file_upload_scan_attributes_are_set(self, mock_DS, scan_service, filename):
        scan_service, retrieved_scans, scan = self.setup_tests(scan_service, filename)
        num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = scan_service.param
        assert scan.xnat_scan_id == scan_id
        assert scan.xnat_uri == scan_uri

@pytest.mark.parametrize('filename,import_service,resource_type',
                         [('T1.nii.gz', False, 'NIFTI'), ('structural.nii', False, 'NIFTI'),
                          ('DICOMS.zip', True, 'DICOM')])
class TestScanUploadPrivateMethods(ScanUploadSetup):
    """A class to test selected private methods called by the public add method.

    The class level parameters are the filename, a boolean indicating whether the import_service should be invoked,
    i.e., the files are dicoms, and the resource label to be passed to XNAT.

    The mocked_scan_service fixture is parametrized at the test level in this class.
    """

    @pytest.mark.parametrize('scan_service', small_set_of_params, indirect=True)
    @mock.patch('cookiecutter_mbam.scan.service.DerivationService')
    def test_resource_name_accords_to_file_type(self, mock_DS, scan_service, filename, import_service, resource_type):
        scan_service = scan_service(do_mock=True)
        scan_service = self.add_a_scan(scan_service, filename)
        scan_service._generate_xnat_identifiers.assert_called_with(dcm=import_service)
        xnat_ids = scan_service._generate_xnat_identifiers(dcm=import_service)
        assert xnat_ids['resource']['xnat_id'] == resource_type

    @pytest.mark.parametrize('scan_service', small_set_of_params, indirect=True)
    def test_process_file(self, scan_service, filename, import_service, resource_type):
        scan_service = scan_service(do_mock=True)
        scan_service, file = self.open_file_storage_obj(scan_service, filename)
        file_path, imp = scan_service._process_file(file)
        assert imp == import_service
        if filename == 'structural.nii':
            filename = 'structural.nii.gz'
        assert file_path == os.path.join(scan_service.upload_dest, filename)
        file.close()

    @pytest.mark.parametrize('scan_service', large_set_of_params, indirect=True)
    def test_generate_xnat_ids(self, scan_service, filename, import_service, resource_type):
        scan_service = scan_service(do_mock=True)
        num_exp, num_scans, exp_id, scan_id, exp_uri, scan_uri = scan_service.param
        xnat_ids = scan_service._generate_xnat_identifiers()
        assert xnat_ids['experiment']['xnat_id'] == exp_id
        assert xnat_ids['scan']['xnat_id'] == scan_id

class TestScanUtils:
    """A class to test utility functions called by the scan service"""

    @pytest.mark.parametrize('scan_service', small_set_of_params, indirect=True)
    def test_gzip(self, scan_service):
        """
        When the gzip utility function is called with a path to a file
        It returns a gzipped file object and the path to that file on disk
        And the file name of the new gzipped file is the old file name + the .gz extension
        """
        scan_service = scan_service(do_mock=True)
        nii_path = os.path.join(scan_service.instance_path, 'files', 'structural.nii')
        file_object, file_path = gzip_file(nii_path)
        assert type(file_object).__name__ == 'GzipFile'
        assert os.path.basename(file_path) == 'structural.nii.gz'
        os.remove(file_path)

@pytest.mark.parametrize('scan_service', small_set_of_params, indirect=True)
class TestDicomConversion(ScanUploadSetup):

    def test_when_nifti_file_passed_to_scan_service_launch_response_is_not_set(self, scan_service):
        scan_service, retrieved_scans, scan = self.setup_tests(scan_service, 'T1.nii.gz')
        assert not hasattr(scan_service, 'launch_response')

    @mock.patch('cookiecutter_mbam.derivation.service.XNATConnection')
    def test_when_dicoms_are_passed_to_scan_service_launch_response_is_set(self, test_xc_class, scan_service):
        url = crop(small_set_of_params[0][-1], '/experiment')
        rv = {'command_id': 28, 'status': 'success', 'type': 'container', 'params': {'scan': url}}
        mock_xc = mock.MagicMock()
        mock_xc.launch_command.return_value = rv
        test_xc_class.return_value = mock_xc
        scan_service, retrieved_scans, scan = self.setup_tests(scan_service, 'DICOMS.zip')
        assert scan_service.launch_response == rv




