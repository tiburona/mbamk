# -*- coding: utf-8 -*-
"""Scan model."""

from cookiecutter_mbam.database import Model, SurrogatePK, db, reference_col, relationship
from cookiecutter_mbam.utils.model_utils import make_ins_del_listener
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
    xnat_label = db.Column(db.String(80))
    orig_aws_key = db.Column(db.String(255))
    experiment_id = reference_col('experiment', nullable=True)

    def __init__(self, experiment_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, experiment_id=experiment_id, **kwargs)

    #todo figure out how to put experiment date in the repr
    def __repr__(self):
        """Represent instance as a unique string."""
        return f'<Scan(xnat_uri: {self.xnat_uri})>'


