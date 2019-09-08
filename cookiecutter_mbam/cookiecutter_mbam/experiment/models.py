# -*- coding: utf-8 -*-
"""Experiment model."""

from cookiecutter_mbam.database import Column, Model, SurrogatePK, db, reference_col, relationship
from flask_sqlalchemy import event
from cookiecutter_mbam.user import User
from cookiecutter_mbam.scan import Scan
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
    scans = relationship('Scan', backref='experiment')

    def __init__(self, date, scanner, user_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, date=date, scanner=scanner, user_id=user_id, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Experiment({date})>'.format(date=self.date)


@event.listens_for(Experiment, "after_insert")
def after_insert_listener(mapper, connection, target):
    user = User.get_by_id(target.user_id)
    num_experiments = user.num_experiments + 1
    user_table = User.__table__
    connection.execute(
        user_table
        .update()
        .where(user_table.c.id == target.user_id)
        .values(num_experiments=num_experiments)
    )


@event.listens_for(Experiment, "after_delete")
def after_insert_listener(mapper, connection, target):
    user = User.get_by_id(target.user_id)
    num_experiments = user.num_experiments - 1
    user_table = User.__table__
    connection.execute(
        user_table
        .update()
        .where(user_table.c.id == target.user_id)
        .values(num_experiments=num_experiments)
    )


@event.listens_for(Scan, "after_insert")
def after_insert_listener(mapper, connection, target):
    experiment = Experiment.get_by_id(target.experiment_id)
    num_scans = experiment.num_scans + 1
    experiment_table = Experiment.__table__
    connection.execute(
        experiment_table
        .update()
        .where(experiment_table.c.id == target.experiment_id)
        .values(num_scans=num_scans)
    )

delete_listener = make_ins_del_listener(Scan, Experiment, 'scan', 'experiment', 'after_delete', -1)