# -*- coding: utf-8 -*-
"""Experiment service.
"""

from .models import Experiment

class ExperimentService:

    def add(self, user, date, scanner, field_strength):
        exp = Experiment.create(date=date, scanner=scanner, field_strength=field_strength, user_id=user.id)
        return exp
