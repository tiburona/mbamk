# -*- coding: utf-8 -*-
"""Model unit tests."""
import datetime as dt
from cookiecutter_mbam.utils import send_email
from cookiecutter_mbam.app import mail

class TestMail:
    """Mail unit test."""

    def test_send_mail(self, testapp):
        with mail.record_messages() as outbox:

            mail.send_message(subject='testing',
                              body='test',
                              recipients=['foo@example.com'])

            assert len(outbox) == 1
            assert outbox[0].subject == "testing"
