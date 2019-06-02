# def _xnat_chain(self):
#     """Construct the celery chain that performs XNAT functions and updates MBAM database with XNAT IDs
#
#     Constructs the chain to upload a file to XNAT and update user, experiment, and scan representations in the MBAM
#     database, and if the file is a dicom, append to that chain a chain that conducts dicom conversion, and finally
#     set the error handler on the chain.
#
#     :return: Celery chain that performs XNAT functions
#     """
#
#     email_info = (MAIL_PASSWORD, self.user.email, "Something went wrong with XNAT.")
#
#     xnat_upload_chain = chain(
#         self.xc.upload_chain(file_path=self.local_path, import_service=self.dcm),
#         self._update_database_objects_sig()
#     )
#
#     if self.dcm:
#         dicom_conversion_chain = self._dicom_conversion_chain(self.scan)
#         xnat_chain = chain(xnat_upload_chain, dicom_conversion_chain)
#     else:
#         xnat_chain = xnat_upload_chain
#
#     return xnat_chain.set(link_error=error_handler.s(email_info))


# You could choose to test this method by mocking chain and its constituents, executing this subchain, and then checking
# that the the constituents were called with the arguments you expect.
# You could also execute the chain synchronously, mock any requests, and test the result.


from cookiecutter_mbam import celery

class TestXNATChain:



