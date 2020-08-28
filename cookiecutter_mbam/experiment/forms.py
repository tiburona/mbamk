# -*- coding: utf-8 -*-
"""Experiment forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import SelectField, FileField, SubmitField
from wtforms.fields.html5 import DateField


class ExperimentForm(FlaskForm):
    """Experiment form."""

    date = DateField('Scan date', format='%Y-%m-%d')
    scanner = SelectField('Scanner',
                          choices=[('Unknown','Don\'t know'),('GE', 'GE'), ('Sie', 'Siemens'), ('Phi', 'Phillips')],
                          default='Unknown')
    field_strength = SelectField('Field strength',
                                 choices=[('Unknown','Don\'t know'),('1.5T', '1.5T'), ('3T', '3T'), ('7T', '7T')],
                                 default='Unknown')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(ExperimentForm, self).validate()


class ScanForm(FlaskForm):
    """Scan form."""

    scan_file = FileField(validators=[FileAllowed(['nii', 'nii.gz', 'zip'], 'Allowed file types only!')])
    submit = SubmitField('Upload')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ScanForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(ScanForm, self).validate()


class ExperimentAndScanForm(ExperimentForm, ScanForm):
    """Experiment and scan Ffrm"""

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentAndScanForm, self).__init__(*args, **kwargs)


