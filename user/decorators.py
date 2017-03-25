from functools import wraps
from flask import session, request, redirect, url_for, abort

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
    
def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = kwargs['user_id']
        if session.get('user_id') != user_id:
            return redirect(url_for('scan_view', user_id=session.get('user_id')))
            #abort(403)
        return f(*args, **kwargs)
    return decorated_function
    
    
def set_vars(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if session.get('user_id'):
            user_id=session.get('user_id')
            SUBJECT=str(user_id).zfill(4)
            #return SUBJECT, user_id
        return f(*args, **kwargs)
    return decorated_function        