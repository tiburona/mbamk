from .app import create_app
from celery import group, chain
from scratch import celery
from .init_celery import init_celery
from .test_celery import foo, bar, baz

app = create_app()
init_celery(app, celery)

job = group([foo.s(1, 2), bar.s( 3, 4)]) | baz.s(5)

job.apply_async()






