from .models import Derivation
from .tasks import *
from celery import chain
from cookiecutter_mbam.base import BaseService

tasks = {'set_attribute': set_derivation_attribute, 'get_attribute': get_derivation_attribute,
         'set_attributes': set_derivation_attributes}


class DerivationService(BaseService):

    def __init__(self, scans, process_name, tasks=tasks):
        super().__init__(Derivation)
        self.scans = scans
        self.tasks = tasks
        self.process_name = process_name
        self.derivation = Derivation.create(scans=self.scans, process_name=process_name, container_status='Pending')
    
    def _raise_exception_if_process_fails(self):
        return raise_exception.s(whitelist=['Complete'])

    def update_derivation_model(self, key, exception_on_failure=False):
        if exception_on_failure:
            return chain(
                self.set_attribute(self.derivation.id, key, passed_val=True),
                self._raise_exception_if_process_fails()
            )
        else:
            return self.set_attribute(self.derivation.id, key, passed_val=True)

    def construct_derivation_uri_from_scan_uri(self, suffix):
        return construct_derivation_uri_from_scan_uri.si(self.derivation.id, suffix)
