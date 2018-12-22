# -*- coding: utf-8 -*-
"""Scan forms."""

from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


class ScanForm(FlaskForm):
    scan_file = FileField(validators=[FileAllowed(['nii', 'nii.gz', 'zip']), FileRequired()])
    submit = SubmitField('Submit')




