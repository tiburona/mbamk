from .config import config_by_name, config_name

def init_celery(app, celery):
    """Add flask app context to celery.Task"""
    # This method taken from this SO answer: https://stackoverflow.com/a/50666542/2066083
    celery.config_from_object(config_by_name[config_name])
    TaskBase = celery.Task
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery