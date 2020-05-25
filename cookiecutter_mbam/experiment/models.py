# -*- coding: utf-8 -*-
"""Experiment model."""

from cookiecutter_mbam.database import Column, Model, SurrogatePK, db, reference_col, relationship
from cookiecutter_mbam.scan.models import Scan
from cookiecutter_mbam.user import User
from cookiecutter_mbam.utils.model_utils import make_ins_del_listener

from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class Experiment(SurrogatePK, Model):
    """A user's experiment, during which they are scanned."""

    __tablename__ = 'experiment'
    date = Column(db.Date(), nullable=False)
    scanner = Column(db.String(80), nullable=True)
    field_strength = Column(db.String(80), nullable=True)
    num_scans = Column(db.Integer(), nullable=True, default=0)
    xnat_id = Column(db.String(80), nullable=True)
    xnat_label = Column(db.String(80), nullable=True)
    xnat_uri = Column(db.String(255), nullable=True)
    user_id = reference_col('user', nullable=False)
    scans = relationship('Scan', backref='experiment', lazy='dynamic')
    scan_counter = Column(db.Integer(), default=0)
    visible = Column(db.Boolean(), nullable=True)

    def __init__(self, date, scanner, user_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, date=date, user_id=user_id, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Experiment({date})>'.format(date=self.date)



scan_insert_listener = make_ins_del_listener(Scan, Experiment, 'scan', 'experiment', 'after_insert', 1, count=True)

scan_delete_listener = make_ins_del_listener(Scan, Experiment, 'scan', 'experiment', 'after_delete', -1)

experiment_insert_listener = make_ins_del_listener(Experiment, User, 'experiment', 'user', 'after_insert', 1,
                                                   count=True)

experiment_delete_listener = make_ins_del_listener(Experiment, User, 'experiment', 'user', 'after_delete', -1)
