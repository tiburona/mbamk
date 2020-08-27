# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
# See https://github.com/mattupstate/flask-security/blob/develop/flask_security/forms.py
from flask_security.forms import RegisterForm, ForgotPasswordForm, ResetPasswordForm
from wtforms.fields.html5 import DateField, EmailField
from wtforms import StringField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length


class ProfileForm(FlaskForm):
    """ Basic user profile form. """
    first_name = StringField('First Name', validators=[Length(min=2, max=25)])
    last_name = StringField('Last Name', validators=[Length(min=2, max=25)])
    sex = SelectField('Sex',
                      choices=[(None, ''), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
                      validators=[DataRequired()])
    dob = DateField('Date of Birth (mm/dd/YYYY).', format='%Y-%m-%d', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ProfileForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        return super(ProfileForm, self).validate()


class ConsentForm(FlaskForm):
    """ Consent to participation in research form. """
    consented = BooleanField('Consent', validators=[DataRequired()])


class AssentForm(FlaskForm):
    """ Assent to participation in research form. """
    assented = BooleanField('Assent', validators=[DataRequired()])
    email = EmailField('Parent Email Address (required)', validators=[DataRequired(), Email()])
