from flask_wtf import Form
from wtforms import validators, StringField, PasswordField, SelectField, DateField
from wtforms.fields.html5 import EmailField

class RegisterForm(Form):
    fullname = StringField('Full Name *', [validators.InputRequired()])
    email = EmailField('Email *', [validators.Required(), validators.Email()])
    username = StringField('Username *', [
        validators.Required(),
        validators.Length(min=4, max=25)
        ])
    password = PasswordField('New Password *', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Length(min=4, max=80)
        ])
    confirm = PasswordField('Repeat Password *')
    sex = SelectField('Sex *', choices=[('Male','Male'),('Female','Female')])
    age = StringField('Age', [
        validators.Optional(),
        validators.Length(max=3)
        ])
    dob = DateField('Date of Birth (mm/dd/yyyy)', validators=[validators.Optional()], format='%m/%d/%Y', )
    #dob = DateTimeField('Date',validators=[DateRange(min=datetime(1900, 1, 1),max=datetime(2000, 10, 10))])
    #dob = DateTimeField('Date')
    
class LoginForm(Form):
    username = StringField('Username', [
        validators.Required(),
        validators.Length(min=4, max=24)
        ])
    password = PasswordField('Password', [
        validators.Required(),
        validators.Length(min=4,max=80)
        ])