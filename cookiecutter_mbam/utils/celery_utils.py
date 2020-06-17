from celery import Celery
import functools
#from cookiecutter_mbam.scan.service import ScanService
from cookiecutter_mbam.base.tasks import send_email
from flask_security import current_user

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

def unpack_tuple(f):
    # this method taken from this blogpost: https://wiredcraft.com/blog/3-gotchas-for-celery/
    @functools.wraps(f)
    def _wrapper(*args, **kwargs):
        if len(args) > 0 and type(args[0]) == tuple:
            args = args[0] + args[1:]
        return f(*args, **kwargs)
    return _wrapper

class ErrorTask(Task):
     #abstract=True
     # From https://github.com/celery/celery/issues/1282
     # def __init__(self):
     # #     self.run = add_kwarg(self.run)
     #     self.previous_exc=None
    def __init__(self, user):
        self.user = current_user

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # exc (Exception) - The exception raised by the task.
        # args (Tuple) - Original arguments for the task that Failed
        # kwargs (Dict) - Original keyword arguments for the task that Failed
        print('OK HERE {0!r} failed: {1!r}'.format(task_id, exc))
        #exp_id=1
        #user_id = str(current_user.get_id())
        #ScanService(user_id, exp_id)._error_proc('')
        #ss._error_proc('xnat_status')
        subject='subject'
        body='body'
        message = {'subject': subject,'body': body}
        send_email(('My Name',self.user.email, message))
