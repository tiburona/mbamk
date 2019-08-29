from celery import group, chord
from scratch.tasks import foo, bar, baz, bif

job = group([foo.s(1, 2), bar.s(3, 4)]) | baz.s(5) | bif.s()

job.apply_async()



