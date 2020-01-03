# -*- coding: utf-8 -*-
"""Scan forms."""

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, DateField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from cookiecutter_mbam.experiment.forms import ExperimentForm

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


class ScanForm(FlaskForm):
    scan_file = FileField(validators=[FileAllowed(['nii', 'nii.gz', 'zip'])])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ScanForm, self).__init__(*args, **kwargs)

class ExperimentAndScanForm(ExperimentForm, ScanForm):

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentAndScanForm, self).__init__(*args, **kwargs)




