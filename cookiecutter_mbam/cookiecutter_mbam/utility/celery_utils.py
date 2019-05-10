from celery import Celery
from cookiecutter_mbam import celery
import os
import functools
import smtplib, ssl


def init_celery(app, celery):
    """Add flask app context to celery.Task"""
    # This method taken from this SO answer: https://stackoverflow.com/a/50666542/2066083
    celery.config_from_object('cookiecutter_mbam.celeryconfig')
    TaskBase = celery.Task
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def get_celery_worker_status(app):
 i = app.control.inspect()
 stats = i.stats()
 registered_tasks = i.registered()
 active_tasks = i.active()
 scheduled_tasks = i.scheduled()
 result = {
  'stats': stats,
  'registered_tasks': registered_tasks,
  'active_tasks': active_tasks,
  'scheduled_tasks': scheduled_tasks
 }
 return result

@celery.task
def update_model(val, class_name, instance_id, key):
    instance = class_name.get_by_id(instance_id)
    args = {key: val}
    instance.update(**args)
    return val

def unpack_tuple(f):
    # this method taken from this blogpost: https://wiredcraft.com/blog/3-gotchas-for-celery/
    @functools.wraps(f)
    def _wrapper(*args, **kwargs):
        if len(args) > 0 and type(args[0]) == tuple:
            args = args[0] + args[1:]
        return f(*args, **kwargs)
    return _wrapper


@celery.task
def log_error(task_id):
    result = celery.AsyncResult(task_id)
    result.get(propagate=False)  # make sure result written.
    with open(os.path.join('/var/errors', task_id), 'a') as fh:
        fh.write('--\n\n%s %s %s' % (
            task_id, result.result, result.traceback))

@celery.task
def send_email(email_info):
    password, recipient, message = email_info
    port = 587
    smtp_server = "smtp.gmail.com"
    sender_email = "testingmbam@gmail.com"
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient, message)
    return

@celery.task
def error_handler(request, exc, traceback, email_info):
    print("THE REQUEST IS", request)
    print("THE EXC IS", exc)
    print("THE TRACEBACK IS", traceback)
    send_email(email_info)
    return "an error"