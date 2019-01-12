from cookiecutter_mbam.xnat import XNATConnection
from .models import Derivation
import configparser
import os
from flask import current_app

process_to_command = {
    'dicom_to_nifti':'dcm2niix'
}

class DerivationService:

    def __init__(self, derivation_id, scan_id, config_dir = ''):
        self.derivation_id = derivation_id
        self.derivation = Derivation.get_by_id(derivation_id)
        self.scan_id = scan_id
        self.process_name = self.derivation.process_name
        self.instance_path = current_app.instance_path[:-8]
        if not len(config_dir):
            config_dir = self.instance_path
        self._config_read(os.path.join(config_dir, 'setup.cfg'))
        self.process_to_command = process_to_command

    def _config_read(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        self.xc = XNATConnection(config=config['XNAT'])
        self.command_config = config['commands']

    # Does the translation of command name to ids belong here or in the XNAT service?
    def launch(self, data=None):
        command_id = self.command_config[self.process_name+ '_command_id']
        wrapper_id = self.command_config[self.process_name + '_wrapper_id']
        self.derivation.status = 'started'
        self.xc.launch_command(command_id, wrapper_id, data)

