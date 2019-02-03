# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import FlaskForm
from flask_security.forms import LoginForm
from wtforms.fields.html5 import EmailField
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Required, InputRequired

from cookiecutter_mbam.user.models import User

class ContactForm(FlaskForm):
    """ Contact form. """
    fullname = StringField('Full Name (required)', [InputRequired()])
    email = EmailField('Contact Email (required)', [Required(), Email()])
    subject = SelectField('Subject', choices=[('General Inquiry','General Inquiry'),('Site Suggestion','Site Suggestion'),('Other','Other')])
    message = TextAreaField('Message (required)', [InputRequired(), Length(max=500)])
