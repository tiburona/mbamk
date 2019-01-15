# -*- coding: utf-8 -*-
"""Experiment views."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_security import current_user
from .models import Experiment
from .forms import ExperimentForm
from .service import ExperimentService
from cookiecutter_mbam.utils import flash_errors

blueprint = Blueprint('experiment', __name__, url_prefix='/experiments', static_folder='../static')

def add_experiment(form):
    """Add an experiment"""
    exp = ExperimentService().add(date=form.date.data, scanner=form.scanner.data,
                                  field_strength=form.field_strength.data, user=current_user)
    flash('You successfully created a new experiment.', 'success')
    session['curr_experiment'] = exp.id
    return exp.id

@blueprint.route('/')
def experiments():
    """List experiments."""
    experiments = Experiment.query.all()
    return render_template('experiments/experiments.html', experiments=experiments)

@blueprint.route('/add', methods=['GET', 'POST'])
def add():
    """Access the add an experiment route and form."""
    form = ExperimentForm(request.form)
    if form.validate_on_submit():
        exp_id = add_experiment(form)
        return redirect(url_for('experiment.single_experiment', id=exp_id))
    else:
        flash_errors(form)
    return render_template('experiments/new_experiment.html',session_form=form)

@blueprint.route('/<id>', methods=['GET'])
def single_experiment(id):
    """Display a single experiment"""
    return render_template('experiments/experiment.html', id=id)
