import os
import json
import pytest
from .test_scan_upload import ScanUploadSetup, small_set_of_params


@pytest.mark.parametrize('scan_service', small_set_of_params, indirect=True)
class TestXNATUploads(ScanUploadSetup):
    """A class to test that scans can be uploaded to XNAT"""

    def get_test_values(self, scan_service, filename, resource_name):
        scan_service, retrieved_scans, db_scan = self.setup_tests(scan_service, filename, mock=False)
        project, subject, experiment, xnat_scan = scan_service.xc.get_scan_info('000001', '000001_MR1')
        scan_service.xc.refresh_xnat_catalog(experiment.uri)
        url = os.path.join(xnat_scan.uri, 'resources', resource_name, 'files')
        response = scan_service.xc.xnat_get(url)
        scan_service.xc.xnat_delete(experiment.uri)
        files = json.loads(response.content)
        first_file = files['ResultSet']['Result'][0]
        file_size = int(first_file['Size'])
        return (first_file, file_size, xnat_scan, db_scan)

    def common_tests_for_dicom_and_nifti(self, file_size, db_scan, xnat_scan):
        assert db_scan.xnat_uri == xnat_scan.uri
        assert file_size > 1000

    @pytest.mark.parametrize('filename', ['T1.nii.gz', 'structural.nii'])
    def test_nifti_uploads_to_xnat(self, scan_service, filename):
        first_file, file_size, xnat_scan, db_scan = self.get_test_values(scan_service, filename, 'NIFTI')
        self.common_tests_for_dicom_and_nifti(file_size, db_scan, xnat_scan)
        assert first_file['Name'] == 'T1.nii.gz'
        assert 'T1_1' in xnat_scan.uri

    def test_dicom_uploads_to_xnat(self, scan_service):
        first_file, file_size, xnat_scan, db_scan = self.get_test_values(scan_service, 'DICOMS.zip', 'DICOM')
        self.common_tests_for_dicom_and_nifti(file_size, db_scan, xnat_scan)
        assert first_file['file_format'] == 'DICOM'
