# -*- coding: utf-8 -*-
"""Experiment service.
"""

from .models import Experiment

class ExperimentService:

    def add(self, user, date, scanner):
        exp = Experiment.create(date=date, scanner=scanner, user_id=user.id)
        return exp
