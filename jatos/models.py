# coding: utf-8
from flask_brain_db import db
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr

# Use sqlacodegen to generate below based on Jatos MySQL tables. 
#from sqlalchemy import BigInteger,Column, DateTime, =db.ForeignKey,db.Integer, String, Table, text
#from sqlalchemy.orm import relationship
#from sqlalchemy.ext.declarative import declarative_base
#Base = declarative_base()
#metadata = Base.metadata

class Worker(db.Model):
    __tablename__ = 'Worker'

    id = db.Column(db.BigInteger, primary_key=True)
    workerType = db.Column(db.String(31), nullable=False)
    mtWorkerId = db.Column(db.String(255))
    comment = db.Column(db.String(255))
    user_email = db.Column(db.ForeignKey(u'User.email'), index=True)
    
    # Spiro added this
    #user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))
    
    # relationships
    User = db.relationship(u'JatosUser')
    #Muser = db.relationship('Muser')
    
    def __init__(self, workerType, mtWorker, comment, user_email): # user_email is study organizer
        self.workerType = workerType
        self.mtWorker = mtWorker
        self.comment = comment
        self.user_email = user_email
        
    
class JatosUser(db.Model):
    __tablename__ = 'User'

    email =db.Column(db.String(255), primary_key=True)
    name =db.Column(db.String(255))
    passwordHash =db.Column(db.String(255))
    
class Batch(db.Model):
    __tablename__ = 'Batch'

    active =db.Column(db.Integer, nullable=False)
    id =db.Column(db.BigInteger, primary_key=True)
    maxActiveMembers =db.Column(db.Integer)
    maxTotalMembers =db.Column(db.Integer)
    maxTotalWorkers =db.Column(db.Integer)
    study_id=db.Column(db.ForeignKey(u'Study.id'), index=True)
    title =db.Column(db.String(255))
    uuid =db.Column(db.String(255), nullable=False)
    batchList_order =db.Column(db.Integer)

    study = db.relationship(u'Study')
    workers = db.relationship(u'Worker', secondary='BatchWorkerMap')


t_BatchWorkerMap = db.Table(
    'BatchWorkerMap', db.metadata,
    db.Column('batch_id', db.ForeignKey(u'Batch.id'), primary_key=True, nullable=False),
    db.Column('worker_id', db.ForeignKey(u'Worker.id'), primary_key=True, nullable=False, index=True)
)

#class BatchWorkerMap(db.Model):
#    __tablename__ = 'BatchWorkerMap'
#    __bind_key__ = 'jatos'
#    batch_id=db.Column(db.ForeignKey(u'Batch.id'), primary_key=True, nullable=False)
#    worker_id=db.Column(db.ForeignKey(u'Worker.id'), primary_key=True, nullable=False, index=True)

t_Batch_allowedWorkerTypes = db.Table(
    'Batch_allowedWorkerTypes', db.metadata,
    db.Column('batch_id', db.ForeignKey(u'Batch.id'), nullable=False, index=True),
    db.Column('allowedWorkerTypes', db.String(255))
)

#class Batch_allowedWorkerTypes(db.Model):
#    __tablename__ = 'Batch_allowedWorkerTypes'
#    __bind_key__ = 'jatos'
#    batch_id=db.Column(db.ForeignKey(u'Batch.id'), nullable=False, index=True)
#    allowedWorkerTypes=db.Column(db.String(255))

class Component(db.Model):
    __tablename__ = 'Component'

    id =db.Column(db.BigInteger, primary_key=True)
    active =db.Column(db.Integer, nullable=False)
    comments =db.Column(db.String(255))
    date =db.Column(db.DateTime)
    htmlFilePath =db.Column(db.String(255))
    jsonData =db.Column(db.String(255))
    reloadable =db.Column(db.Integer, nullable=False)
    title =db.Column(db.String(255))
    uuid =db.Column(db.String(255), nullable=False)
    study_id =db.Column(db.ForeignKey(u'Study.id'), index=True)
    componentList_order =db.Column(db.Integer)

    study = db.relationship(u'Study')


class ComponentResult(db.Model):
    __tablename__ = 'ComponentResult'

    id =db.Column(db.BigInteger, primary_key=True)
    componentState =db.Column(db.Integer)
    data =db.Column(db.TEXT)
    endDate =db.Column(db.DateTime)
    errorMsg =db.Column(db.String(255))
    startDate =db.Column(db.DateTime)
    component_id =db.Column(db.ForeignKey(u'Component.id'), index=True)
    studyResult_id =db.Column(db.ForeignKey(u'StudyResult.id'), index=True)
    componentResultList_order =db.Column(db.Integer)

    component = db.relationship(u'Component')
    studyResult = db.relationship(u'StudyResult')


class GroupResult(db.Model):
    __tablename__ = 'GroupResult'

    batch_id =db.Column(db.ForeignKey(u'Batch.id'), index=True)
    id =db.Column(db.BigInteger, primary_key=True)
    endDate =db.Column(db.DateTime)
    groupState =db.Column(db.Integer)
    startDate =db.Column(db.DateTime)
    groupSessionData =db.Column(db.String(255))
    groupSessionVersion =db.Column(db.BigInteger, nullable=False)

    batch = db.relationship(u'Batch')


class Study(db.Model):
    __tablename__ = 'Study'

    id =db.Column(db.BigInteger, primary_key=True)
    comments =db.Column(db.String(255))
    date =db.Column(db.DateTime)
    description =db.Column(db.String(255))
    dirName =db.Column(db.String(255))
    jsonData =db.Column(db.String(255))
    locked =db.Column(db.Integer, nullable=False)
    groupStudy =db.Column(db.Integer, nullable=False)
    title =db.Column(db.String(255))
    uuid =db.Column(db.String(255), nullable=False, unique=True)

    User = db.relationship(u'JatosUser', secondary='StudyUserMap')


class StudyResult(db.Model):
    __tablename__ = 'StudyResult'

    id =db.Column(db.BigInteger, primary_key=True)
    abortMsg =db.Column(db.String(255))
    batch_id =db.Column(db.ForeignKey(u'Batch.id'), index=True)
    confirmationCode =db.Column(db.String(255))
    endDate =db.Column(db.DateTime)
    errorMsg =db.Column(db.String(255))
    activeGroupMember_id =db.Column(db.ForeignKey(u'GroupResult.id'), index=True)
    historyGroupMember_id =db.Column(db.ForeignKey(u'GroupResult.id'), index=True)
    startDate =db.Column(db.DateTime)
    studyResultList_order =db.Column(db.Integer)
    studySessionData =db.Column(db.TEXT)
    studyState =db.Column(db.Integer)
    study_id =db.Column(db.ForeignKey(u'Study.id'), index=True)
    worker_id =db.Column(db.ForeignKey(u'Worker.id'), index=True)
    
    activeGroupMember = db.relationship(u'GroupResult', primaryjoin='StudyResult.activeGroupMember_id == GroupResult.id')
    batch = db.relationship(u'Batch')
    historyGroupMember = db.relationship(u'GroupResult', primaryjoin='StudyResult.historyGroupMember_id == GroupResult.id')
    study = db.relationship(u'Study')
    worker = db.relationship(u'Worker')

t_StudyUserMap = db.Table(
    'StudyUserMap', db.metadata,
    db.Column('study_id', db.ForeignKey(u'Study.id'), primary_key=True, nullable=False, index=True),
    db.Column('user_email', db.ForeignKey(u'User.email'), primary_key=True, nullable=False, index=True)
)

#class StudyUserMap(db.Model):
#    __tablename__ = 'StudyUserMap'
#    __bind_key__ = 'jatos'
#    study_id=db.Column(db.ForeignKey(u'Study.id'), primary_key=True, nullable=False, index=True)
#    user_email=db.Column(db.ForeignKey(u'User.email'), primary_key=True, nullable=False, index=True)

class PlayEvolution(db.Model):
    __tablename__ = 'play_evolutions'
 
    id =db.Column(db.Integer, primary_key=True)
    hash =db.Column(db.String(255), nullable=False)
    #applied_at =db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    applied_at =db.Column(db.DateTime, nullable=False, server_default=str(datetime.utcnow()))
    apply_script =db.Column(db.String(255))
    revert_script =db.Column(db.String(255))
    state =db.Column(db.String(255))
    last_problem =db.Column(db.String(255))
