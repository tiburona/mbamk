from .config import Config

def init_celery(app, celery):
    # This method taken from this SO answer: https://stackoverflow.com/a/50666542/2066083
    celery.config_from_object(Config)
    TaskBase = celery.Task
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
