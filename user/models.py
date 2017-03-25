from flask_brain_db import db
from sqlalchemy.ext.declarative import declared_attr

class User(db.Model):
    __tablename__ = 'muser'
    
    id = db.Column(db.BigInteger, primary_key=True)
    fullname = db.Column(db.String(80))
    email = db.Column(db.String(35), unique=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(60))
    sex = db.Column(db.String(35))
    age = db.Column(db.Integer)
    
    dob = db.Column(db.DateTime)
    is_author = db.Column(db.Boolean)
    worker_id = db.Column(db.BigInteger, db.ForeignKey('Worker.id'))

    # relationships
    scans = db.relationship('Scan', backref='user', lazy='dynamic') # one to many
    #JatosWorker = db.relationship('Worker', backref='MBM_User', lazy='dynamic')
    #jatos_worker = db.relationship('Worker', foreign_keys='User.worker_id')
    #comments = db.relationship('Comment', backref='author', lazy='dynamic')
    
    def __init__(self, fullname, email, username, password, sex, age, dob=None, is_author=False,worker_id=None):
        self.fullname = fullname
        self.email = email
        self.username = username
        self.password = password
        self.sex = sex
        self.age = age
        self.dob = dob
        self.is_author = is_author
        self.worker_id=worker_id
        
    def __repr__(self):
        return '<User %r>' % self.username