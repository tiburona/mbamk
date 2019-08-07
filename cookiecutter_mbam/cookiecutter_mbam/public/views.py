# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint, flash, redirect, render_template, url_for


from cookiecutter_mbam.public.forms import ContactForm

blueprint = Blueprint('public', __name__, static_folder='../static')

@blueprint.route('/')
def home():
    """ Home page. """
    return render_template('public/home.html')

@blueprint.route('/FAQ')
def FAQ():
    """ FAQ page. """
    return render_template('public/FAQ.html')

@blueprint.route('/about')
def about():
    """ About page. """
    return render_template('public/about.html')

@blueprint.route('/contact', methods=('GET','POST'))
def contact():
    """ Contact page. """
    form = ContactForm()
    if form.validate_on_submit():
        # Come back to this and complete. Write or use function for sending email
        flash('Message sent. Thank you for contacting us.','success')
        return redirect(url_for('public.home'))
        
    return render_template('public/contact.html',contact_form=form)

# Uncomment below when set up up blogging app
# @blueprint.route('/community')
# def community():
#     return redirect(url_for('blogging.index'))