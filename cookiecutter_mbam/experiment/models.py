# -*- coding: utf-8 -*-
"""Experiment model."""

from datetime import datetime
from cookiecutter_mbam.database import Column, Model, SurrogatePK, db, reference_col, relationship
from cookiecutter_mbam.scan.models import Scan
from cookiecutter_mbam.user import User
from cookiecutter_mbam.utils.model_utils import make_insert_listener
from sqlalchemy.orm import validates
from cookiecutter_mbam.utils.model_utils import date_validator


class Experiment(SurrogatePK, Model):
    """A user's experiment, during which they are scanned."""

    __tablename__ = 'experiment'
    date = Column(db.Date(), nullable=False)
    scanner = Column(db.String(80), nullable=True)
    field_strength = Column(db.String(80), nullable=True)
    xnat_id = Column(db.String(80), nullable=True)
    xnat_label = Column(db.String(80), nullable=True)
    xnat_uri = Column(db.String(255), nullable=True)
    user_id = reference_col('user', nullable=False)
    scans = relationship('Scan', backref='experiment', lazy='dynamic')
    scan_counter = Column(db.Integer(), default=0)
    visible = Column(db.Boolean(), nullable=True)

    def __init__(self, date, user_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, date=date, user_id=user_id, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Experiment({date})>'.format(date=self.date)

    @validates('date')
    def validate_date(self, _, date):
        date_of_first_mr_image = datetime.strptime('1971', '%Y').date()
        return date_validator(date_of_first_mr_image, date)


scan_insert_listener = make_insert_listener(Scan, Experiment, 'scan', 'experiment')

experiment_insert_listener = make_insert_listener(Experiment, User, 'experiment', 'user')
