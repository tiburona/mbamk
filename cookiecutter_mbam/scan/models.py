# -*- coding: utf-8 -*-
"""Scan model."""

from sqlalchemy.orm import validates
from cookiecutter_mbam.database import Model, SurrogatePK, db, reference_col
from cookiecutter_mbam.utils.model_utils import status_validator


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
    label = db.Column(db.String(255), nullable=True)
    visible = db.Column(db.Boolean(), nullable=True)

    def __init__(self, experiment_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, experiment_id=experiment_id, **kwargs)

    # todo figure out how to put experiment date in the repr
    def __repr__(self):
        """Represent instance as a unique string."""
        return f'<Scan(xnat_uri: {self.xnat_uri})>'

    @validates('aws_status')
    def validate_aws_status(self, key, aws_status):
        return status_validator(aws_status, key, ['Pending', 'Uploaded', 'Error'])

    @validates('xnat_status')
    def validate_xnat_status(self, key, xnat_status):
        return status_validator(
            xnat_status, key, ['Pending', 'Uploaded', 'Error']
        )


