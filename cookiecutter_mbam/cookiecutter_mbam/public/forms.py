# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import FlaskForm
from flask_security.forms import LoginForm
from wtforms.fields.html5 import EmailField, DateField
#from wtforms import PasswordField, StringField
#from wtforms import StringField
#from wtforms.validators import DataRequired, Email, Length

from cookiecutter_mbam.user.models import User

# class ContactForm(FlaskForm):
#     """ Contact form. """
#     fullname = StringField('Full Name (required)', [validators.InputRequired()])
#     email = EmailField('Contact Email (required)', [validators.Required(), validators.Email()])
#     subject = SelectField('Subject', choices=[('General Inquiry','General Inquiry'),('Site Suggestion','Site Suggestion'),('Other','Other')])
#     message = TextAreaField('Message (required)', [validators.InputRequired(), validators.Length(max=500)])

# class LoginForm(LoginFormMixin):
#     """Login form."""
#     email = StringField('Email',validators=[DataRequired(), Email(), Length(min=6, max=40)])
#     #username = StringField('Username', validators=[DataRequired()])
#     #password = PasswordField('Password', validators=[DataRequired()])
#
#     def __init__(self, *args, **kwargs):
#         """Create instance."""
#         super(LoginForm, self).__init__(*args, **kwargs)
#         self.user = None
#
#     def validate(self):
#         """Validate the form."""
#         initial_validation = super(LoginForm, self).validate()
#         if not initial_validation:
#             return False
#         #self.user = User.query.filter_by(username=self.username.data).first()
#         self.user = User.query.filter_by(email=self.email.data).first()
#         # if not self.user:
#         #     self.username.errors.append('Unknown username')
#         #     return False
#         if not self.user:
#             self.email.errors.append('Unknown email')
#             return False
#
#         if not self.user.check_password(self.password.data):
#             self.password.errors.append('Invalid password')
#             return False
#
#         if not self.user.active:
#             #self.username.errors.append('User not activated')
#             self.email.errors.append('User not activated')
#             return False
#
#         return True
