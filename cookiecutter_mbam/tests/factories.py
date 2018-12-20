# -*- coding: utf-8 -*-
"""Factories to help in tests."""
import faker, factory
from factory import PostGenerationMethodCall, Sequence, Iterator
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyInteger
from pytest_factoryboy import register

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

@register
class UserFactory(BaseFactory):
    """User factory."""
    email = Sequence(lambda n: 'user{0}@example.com'.format(n))
    password = PostGenerationMethodCall('set_password', 'example')
    active = True

    class Meta:
        """Factory configuration."""
        model = User

@register
class ExperimentFactory(BaseFactory):
    """Experiment Factory."""
    date = fake.date_this_decade(before_today=True, after_today=False)
    scanner = Iterator(['GE', 'Sie', 'Phi'])

    class Meta:
        """Factory configuration."""
        model = Experiment

    user = factory.SubFactory(UserFactory)

@register
class ProfileFactory(UserFactory):
    """Profile factory."""
    first_name = Iterator(['Tom','John','Mary','Ellen'])
    last_name = Iterator(['Smith','Johnson','Patterson','Stoner'])
    sex = Iterator(['Male', 'Female'])
    dob = fake.date_of_birth(tzinfo=None, minimum_age=13, maximum_age=115)
    consent_provided = True
