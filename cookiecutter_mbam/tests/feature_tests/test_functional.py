# -*- coding: utf-8 -*-
"""Functional tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for

from cookiecutter_mbam.user.models import User

from .factories import UserFactory

class TestLoggingIn:
    """Login."""

    def test_can_log_in_returns_200(self, user, testapp):
        """Login successful."""
        # Goes to homepage
        res = testapp.get(url_for('security.login'))
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['email'] = user.email
        form['password'] = 'example'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

    def test_sees_alert_on_log_out(self, user, testapp):
        """Show alert on logout."""
        res = testapp.get(url_for('security.login'))
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['email'] = user.email
        form['password'] = 'example'
        # Submits
        res = form.submit().follow()
        res = testapp.get(url_for('security.logout')).follow()
        # sees /login
        assert 'href="/login"' in res

    def test_sees_error_message_if_password_is_incorrect(self, user, testapp):
        """Show error if password is incorrect."""
        # Goes to homepage
        res = testapp.get(url_for('security.login'))
        # Fills out login form, password incorrect
        form = res.forms['loginForm']
        form['email'] = user.email
        form['password'] = 'wrong'
        # Submits
        res = form.submit()
        # sees error
        assert 'Invalid password' in res

    def test_sees_error_message_if_username_doesnt_exist(self, user, testapp):
        """Show error if username doesn't exist."""
        # Goes to homepage
        res = testapp.get(url_for('security.login'))
        # Fills out login form, password incorrect
        form = res.forms['loginForm']
        form['email'] = 'unknown'
        form['password'] = 'example'
        # Submits
        res = form.submit()
        # sees error
        assert 'Specified user does not exist' in res


class TestRegistering:
    """Register a user."""

    def test_can_register(self, user, testapp):
        """Register a new user."""
        # Goes to homepage
        res = testapp.get('/')
        old_count = len(User.query.all())
        # Clicks Create Account button
        res = res.click('Create account')
        # Fills out the form
        form = res.forms['registerForm']
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        form['password_confirm'] = 'secret'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200
        # A new user was created
        assert len(User.query.all()) == old_count + 1

    def test_sees_error_message_if_passwords_dont_match(self, user, testapp):
        """Show error if passwords don't match."""
        # Goes to registration page
        res = testapp.get(url_for('security.register'))
        # Fills out form, but passwords don't match
        form = res.forms['registerForm']
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        form['password_confirm'] = 'secrets'
        # Submits
        res = form.submit()
        # sees error message
        assert 'Passwords do not match' in res

    def test_sees_error_message_if_user_already_registered(self, user, testapp):
        """Show error if user already registered."""
        user = UserFactory(active=True)  # A registered user
        user.save()
        # Goes to registration page
        res = testapp.get(url_for('security.register'))
        # Fills out form, but username is already registered
        form = res.forms['registerForm']
        form['email'] = user.email
        form['password'] = 'secret'
        form['password_confirm'] = 'secret'
        # Submits
        res = form.submit()
        # sees error
        assert user.email + ' is already associated with an account.' in res

    def test_can_register_logout_login(self, user, testapp):
        """Register a new user, logout, then login."""
        # Goes to homepage
        res = testapp.get('/')
        old_count = len(User.query.all())
        # Clicks Create Account button
        res = res.click('Create account')
        # Fills out the form
        form = res.forms['registerForm']
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        form['password_confirm'] = 'secret'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200
        # A new user was created
        assert len(User.query.all()) == old_count + 1
        # logout user
        res = testapp.get(url_for('security.logout')).follow()
        # log back in
        res = testapp.get(url_for('security.login'))
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

class TestUpdateUserModel:
    """ Updating User model. """

    def test_add_profile(self, user, testapp):
        """ Login and add basic demo info """
        res = testapp.get(url_for('security.login'))
        # Fills out login form
        form = res.forms['loginForm']
        form['email'] = user.email
        form['password'] = 'example'
        # Submits
        res = form.submit().follow()
        # grab profile form
        res = testapp.get(url_for('user.profile'))
        form = res.forms['profileForm']
        form['first_name'] = 'foo'
        form['last_name'] = 'bar'
        form['dob'] = '2002-02-02'
        form['sex'] = 'Female'
        res = form.submit().follow()
        # sees flash message and can retrieve user with new attributes
        assert 'User profile saved' in res
        usr = User.get_by_id(user.id)
        assert usr.sex == 'Female'
