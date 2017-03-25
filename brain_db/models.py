from flask_brain_db import db, uploaded_images
from datetime import datetime
from helpers import create_fk, _find_schema
from sqlalchemy.ext.declarative import declared_attr

#class Brain_db(db.Model):
#    __tablename__ = 'brain_db'

#    id=db.Column(db.Integer, primary_key=True)
#    name=db.Column(db.String(80))
#    admin = db.Column(db.Integer, db.ForeignKey('brain_db.muser.id'))
#    # Learn more about below
#    scans = db.relationship('Scan', backref='brain_db', lazy='dynamic')
#    
#    def __init__(self, name, admin):
#        self.name = name
#        self.admin = admin
#        
#    def __repr__(self):
#        return '<Brain_db %r>' % self.name
        
class Scan(db.Model):
    __tablename__ = 'scan'
    
    id = db.Column(db.BigInteger, primary_key=True)
    # COME BACK TO, FIGURE OUT HOW TO ASSIGN ID FROM XNAT
    # xnat_id = db.Column(db.Integer, db.ForeignKey('mbam.id'))
    #brain_db_id = db.Column(db.Integer, db.ForeignKey('brain_db.brain_db.id'))
    user_id = db.Column(db.BigInteger, db.ForeignKey('muser.id'))
    xnat_subject_id = db.Column(db.String(64))
    xnat_session_id = db.Column(db.String(64))
    title = db.Column(db.String(80))
    uploaded_file = db.Column(db.String(255))
    scan_number = db.Column(db.Integer)
    scan_age = db.Column(db.Integer)
    scan_date = db.Column(db.DateTime)
    upload_date = db.Column(db.DateTime)
    
    struct_subjectSpace=db.Column(db.String(255))
    zscore_subjectSpace=db.Column(db.String(255))
    struct_mniSpace=db.Column(db.String(255))
    zscore_mniSpace=db.Column(db.String(255))
    
    @property # modify property depending on record that you're one. This is so can locate the actual image source on the local directory
    def filesrc(self):
        return uploaded_images.url(self.uploaded_file)
    
    def __init__(self, user, xnat_subject_id, xnat_session_id, title, uploaded_file, 
                scan_number=1, scan_age=None, scan_date=None, upload_date=None,struct_subjectSpace=None,
                zscore_subjectSpace=None,struct_mniSpace=None,zscore_mniSpace=None):
        #self.brain_db_id=brain_db.id
        self.user_id = user.id
        self.xnat_subject_id = xnat_subject_id
        self.xnat_session_id = xnat_session_id
        self.title=title
        self.uploaded_file = uploaded_file
        self.scan_number = scan_number
        self.scan_age = scan_age
        self.scan_date = scan_date
        
        if upload_date is None:
            self.upload_date = datetime.utcnow()
        self.struct_subjectSpace=struct_subjectSpace
        self.zscore_subjectSpace=zscore_subjectSpace
        self.struct_mniSpace=struct_mniSpace
        self.zscore_mniSpace=zscore_mniSpace
        
     
    def __repr__(self):
        return '<Scan %r>' % self.title

#class Category(db.Model):
#    id = db.Column(db.Integer, primary_key = True)
#    name = db.Column(db.String(50))
#    
#    def __init__(self, name):
#        self.name = name
#        
#    def __repr__(self):
#        #return '<Category %r>' % self.name
#        return self.name
        
#class Comment(db.Model):
#    id = db.Column(db.Integer, primary_key = True)
#    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))
#    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))
#    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
#    body = db.Column(db.Text)
#    publish_date = db.Column(db.DateTime)
#    live = db.Column(db.Boolean)
    
#    def __init__(self, blog, post, author, body, publish_date=None, live=True):
#        self.blog_id = blog.id
#        self.post_id = post.id
#        self.author_id = author.id
#        self.body = body
#        if publish_date is None:
#            self.publish_date = datetime.utcnow()
#        self.live = live