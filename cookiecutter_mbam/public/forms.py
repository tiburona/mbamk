# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    """ Contact form. """
    fullname = StringField('Full Name', validators=[Length(min=5, max=50)])
    email = EmailField('Email', validators=[Email()])
    subject = SelectField('Subject',
                          choices=[('General Inquiry', 'General Inquiry'), ('Site Suggestion', 'Site Suggestion'),
                                   ('Other', 'Other')],
                          validators=[DataRequired()])
    message = TextAreaField('Message (required)', validators=[DataRequired(), Length(min=5, max=500)])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ContactForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(ContactForm, self).validate()
