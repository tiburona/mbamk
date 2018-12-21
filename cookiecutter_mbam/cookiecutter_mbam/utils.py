# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash
from threading import Thread
from flask_mail import Message
from flask import current_app

def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)

# Send email using threads,
# See https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xi-email-support
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()
