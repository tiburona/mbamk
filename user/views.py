from flask_brain_db import app, db
from flask import render_template, redirect, url_for, session, request, flash
from user.form import RegisterForm, LoginForm
from user.models import User
from user.decorators import login_required
import bcrypt

@app.route('/login', methods=('GET','POST'))
def login():
    form = LoginForm()
    error = None
    
    if request.method =='GET' and request.args.get('next'):
        session['next'] = request.args.get('next', None)
    
    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data,
            #password=form.password.data
            ).first()
        if user:
            if bcrypt.hashpw(form.password.data, user.password) == user.password:
                session['username'] = form.username.data
                session['is_author'] = user.is_author
                session['user_id'] = user.id
                flash("User %s logged in" % form.username.data)
                if 'next' in session:
                    next = session.get('next')
                    session.pop('next')
                    return redirect(next)
                else:
                    return redirect(url_for('index'))
            else:
                error = "Incorrect username and password"
        else:
            error = "Incorrect username and password"
                
    return render_template('user/login.html', form=form, error=error)
    
@app.route('/register', methods=('GET', 'POST'))
def register():
    form = RegisterForm()
    error=""
    if form.validate_on_submit():
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(form.password.data, salt)
        # user = (self, fullname, email, username, password, sex, age, dob=None, is_author=False,worker_id=None):
        user = User(
        form.fullname.data,
        form.email.data,
        form.username.data,
        hashed_password,
        form.sex.data,
        form.age.data,
        form.dob.data
        )
        
        # first check the user doesn't already exist
        if User.query.filter_by(username=form.username.data).first():
            error = "User already exists"
            return redirect(url_for('register'))
        else:
            db.session.add(user)
            db.session.flush()
        
        if user.id:
            db.session.commit()
            flash("New user registered")
            return redirect(url_for('login'))
        else:
            flash("Error registering new user")
            error="Error creating new user"
            db.session.rollback()
        
    return render_template('user/register.html',form=form)

@app.route('/logout')
def logout():
    session.pop('username')
    session.pop('is_author')
    flash("User logged out")
    return redirect(url_for('index'))