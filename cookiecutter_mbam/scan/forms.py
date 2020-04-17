# -*- coding: utf-8 -*-
"""Scan forms."""

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, DateField, StringField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from cookiecutter_mbam.experiment.forms import ExperimentForm
from wtforms.validators import Length

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


class EditScanForm(FlaskForm):
    label = StringField('Label', validators=[Length(min=2,max=100)])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(EditScanForm, self).__init__(*args, **kwargs)

class ExperimentAndEditScanForm(ExperimentForm, EditScanForm):

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ExperimentAndEditScanForm, self).__init__(*args, **kwargs)
