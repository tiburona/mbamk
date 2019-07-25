from cookiecutter_mbam.base import BaseService
from cookiecutter_mbam.derivation import DerivationService
from cookiecutter_mbam.xnat import XNATConnection
from cookiecutter_mbam.config import config_by_name, config_name
from cookiecutter_mbam.experiment import Experiment
from celery import chain

class OverlayService(BaseService):
    def __init__(self):
        config = config_by_name[config_name]
        self.xc = XNATConnection(config=config.XNAT)

    def _await_fs_recon(self, scans):
        fs_chain = self._fs_recon(scans)
        fs_chain.apply_async(args=[], kwargs={}, time_limit=180000, soft_time_limit=172800)

    def _fs_recon(self, scans):
        self.ds = DerivationService(scans)
        self.ds.create('freesurfer_recon_all')

        experiment = Experiment.get_by_id(scans[0].experiment_id)

        return chain(
            self.xc.create_fs_resource(experiment.xnat_id),
            self.xc.launch_and_poll_for_completion('freesurfer_recon_all'),
            self.ds.update_derivation_model('status', exception_on_failure=True),
        )


