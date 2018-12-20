# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
# See https://github.com/mattupstate/flask-security/blob/develop/flask_security/forms.py
from flask_security.forms import RegisterForm

from wtforms.fields.html5 import DateField
from wtforms import StringField, BooleanField, SelectField
from wtforms.validators import DataRequired, Required, Email, EqualTo, Length

from .models import User

class ProfileForm(FlaskForm):
    """ Profile form. """
    first_name = StringField('First Name', validators=[Length(min=2,max=25)])
    last_name = StringField('Last Name', validators=[Length(min=2, max=25)])
    sex = SelectField('Sex', choices=[('Male','Male'),('Female','Female')], validators=[DataRequired()])
    dob = DateField('Date of Birth (mm/dd/YYYY).', format='%Y-%m-%d', validators=[DataRequired()])
    consent_provided = BooleanField('I have read the <a target=_blank href=/consent>consent form</a>, I agree to participate in this study.',validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ProfileForm, self).__init__(*args, **kwargs)
        #self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(ProfileForm, self).validate()
        if not initial_validation:
            return False

        return True
