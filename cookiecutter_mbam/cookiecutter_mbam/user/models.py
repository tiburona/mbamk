# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from flask_security import UserMixin
from flask_security.utils import verify_password, hash_password

from cookiecutter_mbam.database import Column, Model, Table, SurrogatePK, db, relationship

roles_users = Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(SurrogatePK, Model):
    """A role for a user."""

    __tablename__ = 'role'
    id = Column(db.Integer(), primary_key=True)
    name = Column(db.String(80), unique=True)
    description = Column(db.String(255))

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Role({name})>'.format(name=self.name)

class User(UserMixin, SurrogatePK, Model):
    """A user of the app."""

    __tablename__ = 'user'

    # required for flask-security
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    email = Column(db.String(80), unique=True)
    password = Column(db.String(255))
    active = Column(db.Boolean())
    confirmed_at = Column(db.DateTime())

    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    sex = Column(db.String(30), nullable=True)
    dob = Column(db.DateTime, nullable=True)
    consented = Column(db.Boolean(), default=False)
    assented = Column(db.Boolean(), default=False)
    parent_email = Column(db.String(80), unique=False, nullable=True)

    is_admin = Column(db.Boolean(), default=False)
    xnat_label = Column(db.String(80), nullable=True)
    xnat_uri = Column(db.String(255), nullable=True)
    num_experiments = Column(db.Integer(), default=0)
    roles = db.relationship(
        'Role', secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )

    experiments = relationship('Experiment', backref='user', lazy=True)

    def __init__(self, email, password=None, **kwargs):
        """Create instance."""
        db.Model.__init__(self, email=email, **kwargs)
        if password:
            self.set_password(password)
        else:
            self.password = None

    def set_password(self, password):
        """Set password."""
        self.password = password

    def check_password(self, value):
        """Check password."""
        return verify_password(value,self.password)

    @property
    def full_name(self):
        """Full user name."""
        return '{0} {1}'.format(self.first_name, self.last_name)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User({email!r})>'.format(email=self.email)
