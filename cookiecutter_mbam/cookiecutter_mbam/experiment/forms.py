# -*- coding: utf-8 -*-
"""Experiment forms."""
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField

class ExperimentForm(FlaskForm):
    """Experiment form."""

    date = DateField('Date')

    scanner = SelectField('Scanner', choices=[('GE', 'GE'), ('Sie', 'Siemens'), ('Phi', 'Phillips')])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentForm, self).__init__(*args, **kwargs)

