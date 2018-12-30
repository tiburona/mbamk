# -*- coding: utf-8 -*-
"""Test forms."""

from cookiecutter_mbam.public.forms import LoginForm
from cookiecutter_mbam.user.forms import RegisterForm, ProfileForm

class TestRegisterForm:
    """Register form."""

    def test_validate_user_already_registered(self, user):
        """Enter email that is already registered."""
        form = RegisterForm(email=user.email,
                            password='example', password_confirm='example')

        assert form.validate() is False
        assert user.email + ' is already associated with an account.' in form.email.errors

    def test_validate_success(self, db):
        """Register with success."""
        form = RegisterForm(email='new@test.test',
                            password='example', password_confirm='example')
        assert form.validate() is True

class TestLoginForm:
    """Login form."""

    def test_validate_success(self, user):
        """Login successful."""
        user.set_password('example')
        user.save()
        form = LoginForm(email=user.email, password='example')
        assert form.validate() is True
        assert form.user == user

    def test_validate_unknown_user(self, db):
        """Unknown email."""
        form = LoginForm(email='unknown', password='example')
        assert form.validate() is False
        # Based on messages in https://github.com/mattupstate/flask-security/blob/develop/flask_security/core.py
        assert 'Specified user does not exist' in form.email.errors
        assert form.user is None

    def test_validate_invalid_password(self, user):
        """Invalid password."""
        user.set_password('example')
        user.save()
        form = LoginForm(email=user.email, password='wrongpassword')
        assert form.validate() is False
        assert 'Invalid password' in form.password.errors

    def test_validate_inactive_user(self, user):
        """Inactive user."""
        user.active = False
        user.set_password('example')
        user.save()
        # Correct username and password, but user is not activated
        form = LoginForm(email=user.email, password='example')

        assert form.validate() is False
        assert 'Account is disabled.' in form.email.errors

class TestProfileForm:
    """Profile form."""

    def test_validate_success(self, user):
        """Profile successful."""
        form = ProfileForm(first_name='foo', last_name='bar',
                             sex='Male', dob='1980-05-12', consent_provided=True)

        assert form.validate() is True
