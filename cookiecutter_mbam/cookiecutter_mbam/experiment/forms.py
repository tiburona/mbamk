# -*- coding: utf-8 -*-
"""Experiment forms."""
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField

class ExperimentForm(FlaskForm):
    """Experiment form."""

    date = DateField('Date')

    scanner = SelectField('Scanner', choices=[('ge', 'GE'), ('Siemens', 'Sie'), ('Phi', 'Phillips')])

    num_scans = IntegerField('Number of scan')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentForm, self).__init__(*args, **kwargs)

