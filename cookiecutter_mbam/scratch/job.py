from celery import group
from .test_celery import foo, bar, baz

job = group([foo.s(1, 2), bar.s( 3, 4)]) | baz.s(5)

job.apply_async()

