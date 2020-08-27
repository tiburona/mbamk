# -*- coding: utf-8 -*-
"""Derivation model."""

from sqlalchemy.orm import validates
from cookiecutter_mbam.database import Model, SurrogatePK, db, Table
from cookiecutter_mbam.utils.model_utils import status_validator



derivations_scans = Table(
    'derivations_scans',
    db.Column('scan_id', db.Integer(), db.ForeignKey('scan.id'), primary_key=True),
    db.Column('derivation_id', db.Integer(), db.ForeignKey('derivation.id'), primary_key=True)
)

class Derivation(SurrogatePK, Model):
    """A derivation from a scan."""

    __tablename__ = 'derivation'
    process_name = db.Column(db.String(255), nullable=False)
    xnat_container_id = db.Column(db.String(80), nullable=True)
    cs_id = db.Column(db.String(80), nullable=True)
    xnat_uri = db.Column(db.String(255), nullable=True, unique=True)
    xnat_host = db.Column(db.String(255), nullable=True)
    aws_key = db.Column(db.String(255), nullable=True, unique=True)
    aws_status = db.Column(db.String(255), nullable=False, default='Pending')
    container_status = db.Column(db.String(255), nullable=False)
    scans = db.relationship(
        'Scan', secondary=derivations_scans,
        backref = db.backref('derivations', lazy='dynamic')
        )

    def __init__(self, scans, container_status, **kwargs):
        """Create instance."""
        db.Model.__init__(self, scans=scans, container_status=container_status, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Derivation({uri})>'.format(uri=self.xnat_uri)

    @validates('aws_status')
    def validate_aws_status(self, key, aws_status):
        return status_validator(aws_status, key, ['Pending', 'Uploaded', 'Error'])

    @validates('xnat_status')
    def validate_xnat_status(self, key, xnat_status):
        return status_validator(
            xnat_status, key, ['Pending', 'Complete', 'Failed', 'Killed', 'Killed (Out of Memory)', 'Timed Out']
        )

