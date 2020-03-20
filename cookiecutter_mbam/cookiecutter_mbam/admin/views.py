# -*- coding: utf-8 -*-
"""Admin section, including send a user an email."""
from flask import Blueprint, flash, redirect, render_template, url_for, current_app
from flask_admin import BaseView, expose
from cookiecutter_mbam.utils.error_utils import flash_errors
from flask_security import current_user, roles_required
from cookiecutter_mbam.admin.forms import SendEmailForm
from cookiecutter_mbam.base.tasks import send_email

class EmailView(BaseView):

    # @expose('/')
    # def index(self):
    #     """ Override the master (default) admin dashboard view """
    #     return self.render('admin/index.html')

    @expose('/',methods=('GET','POST'))
    def email(self):
        """ Send email page. Route for someone with admin access to send an email from MBaM to anyone"""
        form = SendEmailForm()
        if form.validate_on_submit():
            fullname=form.fullname.data
            email=form.email.data
            subject=form.subject.data
            body=form.message.data

            message = {'subject': subject,'body': body}
            send_email((fullname,email,message))

            flash('Message sent to ' + fullname,'success')
            return redirect(url_for('admin.index'))

        return self.render('admin/email.html',email_form=form)
