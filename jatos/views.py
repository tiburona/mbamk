# views.py for jspsych modules
from flask_brain_db import app, db
from flask import render_template, redirect, flash, url_for, session, abort, request, current_app, send_from_directory
from user.models import User
#from brain_db.models import Brain_db #, Scan
from user.decorators import login_required, owner_required
import bcrypt
from slugify import slugify
import os
from jatos.models import Study, Worker
from jatos.models import JatosUser # as JatosUser
#db.Model.metadata.reflect(db.engine) 

SCANS_PER_PAGE = 10

@app.route('/studies')
@app.route('/studies/<int:page>')
def study_index(page=1):
    studies = Study.query.order_by(Study.title).paginate(page, SCANS_PER_PAGE, False) # must now do posts.items
    return render_template('jatos/studies.html', studies=studies)

@app.route('/study/<int:study_id>')
@login_required
def study(study_id):
    #study = JatosStudy.query.filter_by(id=study_id).first_or_404() # must now do posts.items
    #user = JatosUser.query.filter_by(id=).first_or_404()
    user_id=session['user_id']
    user = User.query.filter_by(id=user_id).first_or_404()
    
    # Here do the logic for attached user to Jator worker id to general the appropriate URL
    if not user.worker_id:
        # Here create new worker if worker_id if not already present
        worker=Worker('PersonalMultiple',None,None,'admin') # in future should set user_email
        db.session.add(worker)
        db.session.flush()
        
        if worker.id: 
            user.worker_id=worker.id
            db.session.commit()
            flash("Assigned Jatos worker id to User")
        else:
            flash("Error assigning Jatos worker id to User")
            error="Error assigning Jatos worker to User"
            db.session.rollback()
            
    Study_URL='http://flask-blog-spiropan.c9users.io:8081/publix/' + str(study_id) + '/start?batchId=1&personalMultipleWorkerId=' + str(user.worker_id) + '&pre'
    #Study_URL='http://flask-blog-spiropan.c9users.io:8081/publix/' + str(study_id) + '/start?batchId=3&personalSingleWorkerId=' + str(worker_id) + '&pre'
    #Study_URL='http://flask-blog-spiropan.c9users.io:8081/publix/' + str(study_id) + '/start?batchId=3&generalSingle&pre'
    #Study_URL='http://flask-blog-spiropan.c9users.io:8081/publix/' + str(study.id) + '/start?batchId=1&generalSingle&pre'
    return render_template('jatos/study.html', Study_URL=Study_URL)

@app.route('/test')
def test():
    user = User.query.filter_by(username='evans').first_or_404()
    user.worker_id=3
    db.session.commit()
    return "Added worker id"
    #user.name='Spiro Pantazatos'
    
    # create new worker
    #worker=Worker("PersonalMultiple",None,"test_comment",None)
    #db.session.add(worker)
    #db.session.commit()
    #return "Added Worker"

@app.route('/test2')
def test2():
    #Study_URL='http://flask-blog-spiropan.c9users.io:8081/publix/1/start?batchId=1&generalSingle&pre'
    Study_URL='http://flask-blog-spiropan.c9users.io:8081/publix/1/start?batchId=1&personalMultipleWorkerId=8'
    return render_template('jatos/study.html',Study_URL=Study_URL)
    
@app.route('/gonogo/<int:user_id>')
def gonogo(user_id):
    user = User.query.filter_by(id=user_id).first_or_404() 
    #return url_for('static', filename='jspsych/demo_experiment/experiment.html')
    #return current_app.send_static_file('jspsych/demo_experiment/experiment.html')
    #return send_from_directory(url_for('static',filename=''), 'jspsych/demo_experiment/experiment.html')
    #return send_from_directory('/home/ubuntu/workspace/flask_brain_db/static/jspsych/demo_experiment','experiment.html')
    return render_template('jspsych/gonogo.html', user=user)
    
