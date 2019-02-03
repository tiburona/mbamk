from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name
    )
    celery.conf.update(app.config)
    celery.conf.update(
        task_serializer='pickle',
        result_serializer='pickle',
        accept_content=['json', 'pickle'],
        result_backend = 'redis://localhost:6379',
        broker_url='redis://localhost:6379'
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

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

