from .models import Derivation
from .tasks import raise_exception, set_derivation_attribute, get_derivation_attribute
from celery import chain
from cookiecutter_mbam.base import BaseService

tasks = {'set_attribute': set_derivation_attribute, 'get_attribute': get_derivation_attribute}

class DerivationService(BaseService):

    def __init__(self, scan_id, tasks=tasks):
        super().__init__(Derivation)
        self.scan_id = scan_id
        self.tasks = tasks

    def create(self, process_name):
        self.derivation = Derivation.create(scan_id=self.scan_id, process_name=process_name, status='pending')
        return self.derivation

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




