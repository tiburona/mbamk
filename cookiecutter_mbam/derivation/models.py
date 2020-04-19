# -*- coding: utf-8 -*-
"""Derivation model."""

from cookiecutter_mbam.database import Model, SurrogatePK, db, Table

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

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
    #todo: fix validations here
    # __table_args__ = (
    #     db.CheckConstraint(status in ['started', 'unstarted', 'completed', 'failed'], name='check_status_valid'),
    #     {})


    def __init__(self, scans, container_status, **kwargs):
        """Create instance."""
        db.Model.__init__(self, scans=scans, container_status=container_status, **kwargs)
        for scan in scans:
            self.scans.append(scan)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Derivation({uri})>'.format(uri=self.xnat_uri)
