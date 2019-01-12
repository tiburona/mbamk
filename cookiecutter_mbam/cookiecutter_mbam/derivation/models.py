# -*- coding: utf-8 -*-
"""Derivation model."""

from cookiecutter_mbam.database import Model, SurrogatePK, db, reference_col
from cookiecutter_mbam.experiment import Experiment
from flask_sqlalchemy import event

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class Derivation(SurrogatePK, Model):
    """A derivation from a scan."""

    __tablename__ = 'derivation'
    process_name = db.Column(db.String(255), nullable=False)
    xnat_uri = db.Column(db.String(255), nullable=True, unique=True)
    scan_id = reference_col('scan', nullable=True)
    status = db.Column(db.String(255), nullable=False)
    # __table_args__ = (
    #     db.CheckConstraint(status in ['started', 'unstarted', 'completed', 'failed'], name='check_status_valid'),
    #     {})

    def __init__(self, scan_id, status, **kwargs):
        """Create instance."""
        db.Model.__init__(self, scan_id=scan_id, status=status, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Derivation({uri})>'.format(uri=self.xnat_uri)