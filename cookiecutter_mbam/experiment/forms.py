# -*- coding: utf-8 -*-
"""Experiment forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import SelectField, FileField, SubmitField, TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired


class ExperimentForm(FlaskForm):
    """Experiment form."""

    date = DateField('Scan date', format='%Y-%m-%d')
    scanner = SelectField('Scanner',
                          choices=[('Unknown','Don\'t know'),('GE', 'GE'), ('Sie', 'Siemens'), ('Phi', 'Phillips')],
                          default='Unknown')
    field_strength = SelectField('Field strength',
                                 choices=[('Unknown','Don\'t know'),('1.5T', '1.5T'), ('3T', '3T'), ('7T', '7T')],
                                 default='Unknown')
    notes = TextAreaField('Notes', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(ExperimentForm, self).validate()


class ScanForm(FlaskForm):
    """Scan form."""

    scan_file = FileField(validators=[FileRequired(), FileAllowed(['nii', 'nii.gz', 'zip'], 'Allowed file types only!')])
    submit = SubmitField('Upload')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ScanForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(ScanForm, self).validate()


class ExperimentAndScanForm(ScanForm, ExperimentForm):
    """Experiment and Scan form."""

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentAndScanForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(ScanForm, self).validate()


class TestForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(TestForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(TestForm, self).validate()

    test_file = FileField(
        validators=[
            FileRequired(), FileAllowed(['nii', 'nii.gz', 'zip'], 'Allowed file types only!')
        ]
    )
    submit = SubmitField('Upload')


class MomForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(MomForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(MomForm, self).validate()

    scan_file = FileField(
    validators=[FileRequired(), FileAllowed(['nii', 'nii.gz', 'zip'], 'Allowed file types only!')])
    submit = SubmitField('Upload')


class DadForm(FlaskForm):
    date = DateField('Scan date', format='%Y-%m-%d')
    scanner = SelectField('Scanner',
                          choices=[('Unknown', 'Don\'t know'), ('GE', 'GE'), ('Sie', 'Siemens'), ('Phi', 'Phillips')],
                          default='Unknown')
    field_strength = SelectField('Field strength',
                                 choices=[('Unknown', 'Don\'t know'), ('1.5T', '1.5T'), ('3T', '3T'), ('7T', '7T')],
                                 default='Unknown')
    notes = TextAreaField('Notes', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(DadForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(DadForm, self).validate()

class KidForm(MomForm, DadForm):
    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(KidForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(MomForm, self).validate() and super(DadForm, self).validate()




