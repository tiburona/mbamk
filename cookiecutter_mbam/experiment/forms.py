# -*- coding: utf-8 -*-
"""Experiment forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import IntegerField, SelectField, FileField, SubmitField
from wtforms.fields.html5 import DateField

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class ExperimentForm(FlaskForm):
    """Experiment form."""

    date = DateField('Date of scan acquisition.', format='%Y-%m-%d')
    scanner = SelectField('Scanner', choices=[('Unknown','Don\'t know'),('GE', 'GE'), ('Sie', 'Siemens'), ('Phi', 'Phillips')])

    field_strength = SelectField('Field strength', choices=[('Unknown','Don\'t know'),('1.5T', '1.5T'), ('3T', '3T'), ('7T', '7T')])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentForm, self).__init__(*args, **kwargs)

class ScanForm(FlaskForm):
    scan_file = FileField(validators=[FileAllowed(['nii', 'nii.gz', 'zip'])])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ScanForm, self).__init__(*args, **kwargs)

class ExperimentAndScanForm(ExperimentForm, ScanForm):

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentAndScanForm, self).__init__(*args, **kwargs)
