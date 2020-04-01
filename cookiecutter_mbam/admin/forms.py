# -*- coding: utf-8 -*-
"""Admin forms."""
from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class SendEmailForm(FlaskForm):
    """ Send email form. """
    fullname = StringField('Recipient Name (required)', validators=[DataRequired(),Length(min=5,max=50)])
    email = EmailField('Recipient Email (required)', validators=[DataRequired(), Email()])
    subject = StringField('Subject (required)', validators=[DataRequired(), Length(min=5,max=50)])
    message = TextAreaField('Message (required)', validators=[DataRequired(), Length(min=5,max=500)])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(SendEmailForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        initial_validation = super(SendEmailForm, self).validate()
        if not initial_validation:
            return False

        return True
