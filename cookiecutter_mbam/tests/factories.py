# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from factory import PostGenerationMethodCall, Sequence, Iterator
from factory.alchemy import SQLAlchemyModelFactory
import faker

from cookiecutter_mbam.database import db
from cookiecutter_mbam.user.models import User
from cookiecutter_mbam.experiment.models import Experiment

fake = faker.Faker()

class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""

        abstract = True
        sqlalchemy_session = db.session


class UserFactory(BaseFactory):
    """User factory."""

    username = Sequence(lambda n: 'user{0}'.format(n))
    email = Sequence(lambda n: 'user{0}@example.com'.format(n))
    password = PostGenerationMethodCall('set_password', 'example')
    active = True

    class Meta:
        """Factory configuration."""

        model = User

class ExperimentFactory(BaseFactory):
    """Experiment Factory."""


    date = fake.date_this_decade(before_today=True, after_today=False)

    scanner = Iterator(['GE', 'Sie', 'Phi'])

    class Meta:
        """Factory configuration."""

        model = Experiment

