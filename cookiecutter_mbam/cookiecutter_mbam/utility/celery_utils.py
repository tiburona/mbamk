from celery import Celery


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



