# -*- coding: utf-8 -*-
"""Scan model."""

from cookiecutter_mbam.database import Model, SurrogatePK, db, reference_col, relationship

class Scan(SurrogatePK, Model):
    """A user's scan."""

    __tablename__ = 'scan'
    xnat_uri = db.Column(db.String(255))
    experiment_id = reference_col('experiments', nullable=True)
    experiment = relationship('Experiment', backref='scans')

    def __init__(self, experiment_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, experiment_id=experiment_id, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Scan({uri})>'.format(uri=self.xnat_uri)
