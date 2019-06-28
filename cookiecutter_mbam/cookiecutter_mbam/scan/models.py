# -*- coding: utf-8 -*-
"""Scan model."""

from cookiecutter_mbam.database import Model, SurrogatePK, db, reference_col, relationship
from cookiecutter_mbam.utils.model_utils import make_ins_del_listener
from cookiecutter_mbam.experiment import Experiment
from flask_sqlalchemy import event

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class Scan(SurrogatePK, Model):
    """A user's scan."""

    __tablename__ = 'scan'
    xnat_status = db.Column(db.String(80))
    aws_status = db.Column(db.String(80))
    xnat_uri = db.Column(db.String(255))
    xnat_id = db.Column(db.String(80))
    orig_aws_key = db.Column(db.String(255))
    experiment_id = reference_col('experiment', nullable=True)
    derivations = relationship('Derivation', backref='scan')

    def __init__(self, experiment_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, experiment_id=experiment_id, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        experiment_date = Experiment.get_by_id(self.experiment_id).date
        return f'<Scan(date: {experiment_date} xnat_uri: {self.xnat_uri})>'

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
