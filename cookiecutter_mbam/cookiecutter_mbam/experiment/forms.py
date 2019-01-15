# -*- coding: utf-8 -*-
"""Experiment forms."""
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField

from flask import current_app


def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class ExperimentForm(FlaskForm):
    """Experiment form."""

    date = DateField('Date')

    scanner = SelectField('Scanner', choices=[('GE', 'GE'), ('Sie', 'Siemens'), ('Phi', 'Phillips')])

    field_strength = SelectField('FieldStrength', choices=[('1.5T', '1.5T'), ('3T', '3T'), ('7T', '7T')])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentForm, self).__init__(*args, **kwargs)




