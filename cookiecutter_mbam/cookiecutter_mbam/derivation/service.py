from cookiecutter_mbam.xnat import XNATConnection
from .models import Derivation
import configparser
import os
import json
from flask import current_app


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

    def _config_read(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        self.xc = XNATConnection(config=config['XNAT'])
        self.command_config = config['commands']

    # A note about this method and this entire class: right now it arguably looks like like unnecessary wrapping.  Its functions
    # could be wrapped into Scan Service.  I think it will make sense with time.
    def launch(self, data=None):
        """Launch a command
        Generates command id and wrapper id strings to pass to XNAT, sets the derivation status to indicate the process
        is launched, and calls the XNAT Connection method to launch the command.
        :param data:
        :return:
        """
        command_id = self.command_config[self.process_name+ '_command_id']
        wrapper_id = self.command_config[self.process_name + '_wrapper_id']
        self.derivation.status = 'started'
        rv = self.xc.launch_command(command_id, wrapper_id, data)
        return json.loads(rv.text)['container-id']



