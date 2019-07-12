# -*- coding: utf-8 -*-
"""Experiment service.
"""

from .models import Experiment
from cookiecutter_mbam.base import BaseService
from .tasks import set_experiment_attribute, get_experiment_attribute

tasks = {'set_attribute': set_experiment_attribute, 'get_attribute': get_experiment_attribute}

class ExperimentService(BaseService):

    def __init__(self, tasks=tasks):
        super().__init__(Experiment)
        self.tasks = tasks

    def add(self, user, date, scanner, field_strength):
        exp = Experiment.create(date=date, scanner=scanner, field_strength=field_strength, user_id=user.id)
        return exp
