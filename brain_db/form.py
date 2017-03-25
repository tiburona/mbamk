from flask_wtf import Form
from wtforms import StringField, validators, TextAreaField, SelectField, IntegerField, DateField
from user.form import RegisterForm
from brain_db.models import Scan
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed

# Got this from the web to try and enforce unique entries    
class Unique(object):
    """ validator that checks field uniqueness """
    def __init__(self, model, field, message=None):
        self.model = model
        self.field = field
        if not message:
            message = u'this element already exists'
        self.message = message

    def __call__(self, form, field):         
        check = self.model.query.filter(self.field == field.data).first()
        if check:
            raise validators.ValidationError(self.message)

class SetupForm(RegisterForm):
    name = StringField('Brain DB name', [
        validators.Required(),
        validators.Length(max=80)
        ])
        
class ScanForm(Form):
    uploaded_file = FileField('Image (.nii or .zip of dicoms) *', validators=[
        FileAllowed(['jpg','png','gif','nii','nii.gz','zip'], 'Images only!')
        ])
    title = StringField('Short Description *', [
        validators.required(),
        #Unique(Post, Post.title), Doesn't work when updating :(
        validators.Length(max=80)
        ])
    #scan_number =  IntegerField('Scan Number (default is 1, enter 2 or higher for additional scans)', [
    # In future make it so that 2 is only available if 1 scan already in DB
    scan_number = SelectField("Scan Number (default is 1, enter 2 for second scan)", coerce=int, choices=[(1, "1"), (2, "2")], default=1) #, [
        #validators.Optional(),
        #validators.Length(max=1)
        #])
    scan_date = DateField('Date of the scan (mm/dd/YYYY)', format='%m/%d/%Y', validators=(validators.Optional(),))
    scan_age = StringField('Approximate age when scanned *', [
        validators.Required(),
        validators.Length(max=3)
        ])

#class CommentForm(Form):
#    body = TextAreaField('Content', validators=[validators.Required()])

