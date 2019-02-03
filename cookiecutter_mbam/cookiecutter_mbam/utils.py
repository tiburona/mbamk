# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, current_app
from threading import Thread
from flask_mail import Message
from flask_security import current_user
from celery import Celery

def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)

def user_context_processor():
    """This will automatically inject user object to routes and templates.
    See http://slides.skien.cc/flask-hacks-and-best-practices/#21."""
    if current_user.is_authenticated:
        user = current_user._get_current_object()
    else:
        user = None
    return {
        'user': user,
    }

def send_async_email(app, msg):
    """Helper function to send async email.
    See https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xi-email-support"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    """Helper function to send email.
    See https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xi-email-support"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()

