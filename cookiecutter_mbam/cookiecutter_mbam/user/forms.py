# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
from flask_security.forms import RegisterForm
from wtforms.fields.html5 import DateField#,EmailField,
from wtforms import StringField, BooleanField, SelectField
from wtforms.validators import DataRequired, Required, Email, EqualTo, Length

from .models import User

class ProfileForm(FlaskForm):
    """ Profile form. """
    first_name = StringField('First Name', validators=[Length(min=2,max=25)])
    last_name = StringField('Last Name', validators=[Length(min=2, max=25)])
    sex = SelectField('Sex', choices=[('Male','Male'),('Female','Female')])
    dob = DateField('Date of Birth (mm/dd/YYYY).', format='%Y-%m-%d')
    consent_provided = BooleanField('I have read the <a target=_blank href=/consent>consent form</a> agree to participate in this study.',validators=[Required()])

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

# class RegisterForm(RegisterFormMixin):
#     """Register form."""
# #
# #     username = StringField('Username',
# #                            validators=[DataRequired(), Length(min=3, max=25)])
#     email = StringField('Email', validators=[DataRequired(), Email(), Length(min=6, max=40)])
# #     password = PasswordField('Password',
# #                              validators=[DataRequired(), Length(min=6, max=40)])
# #     confirm = PasswordField('Verify password',
# #                             [DataRequired(), EqualTo('password', message='Passwords must match')])
# #
#     def __init__(self, *args, **kwargs):
#         """Create instance."""
#         super(RegisterForm, self).__init__(*args, **kwargs)
#         self.user = None
#
#     def validate(self):
#         """Validate the form."""
#         initial_validation = super(RegisterForm, self).validate()
#         if not initial_validation:
#             return False
#         # user = User.query.filter_by(username=self.username.data).first()
#         # if user:
#         #     self.username.errors.append('Username already registered')
#         #     return False
#         user = User.query.filter_by(email=self.email.data).first()
#         if user:
#             self.email.errors.append('Email already registered')
#             return False
#         return True
