from celery import Celery, Task
from celery.execute import send_task
import functools
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
