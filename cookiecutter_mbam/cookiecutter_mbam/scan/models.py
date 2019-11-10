# -*- coding: utf-8 -*-
"""Scan model."""

from cookiecutter_mbam.database import Model, SurrogatePK, db, reference_col, relationship
from cookiecutter_mbam.utils.model_utils import make_ins_del_listener
from flask_sqlalchemy import event

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


# Todo: figure out model validation in Flask
class Scan(SurrogatePK, Model):
    """A user's scan."""

    __tablename__ = 'scan'
    xnat_status = db.Column(db.String(80), nullable=False, default='Pending')
    aws_status = db.Column(db.String(80), nullable=False, default='Pending')
    xnat_id = db.Column(db.String(80), nullable=True)
    xnat_uri = db.Column(db.String(255), nullable=True)
    aws_key = db.Column(db.String(255), nullable=True)
    experiment_id = reference_col('experiment', nullable=True)
    user_id = reference_col('user', nullable=False)

    def __init__(self, experiment_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, experiment_id=experiment_id, **kwargs)

    #todo figure out how to put experiment date in the repr
    def __repr__(self):
        """Represent instance as a unique string."""
        return f'<Scan(xnat_uri: {self.xnat_uri})>'


