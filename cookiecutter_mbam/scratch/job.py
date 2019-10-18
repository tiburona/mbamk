from functools import reduce
from celery import chain
from celery import Celery
from tasks import *
#from scratch.tasks import cel, foo, bar, baz, bif




def make_chain(num):
    sub_chain_to_run = chain(foo.si(num, num), bar.s(num), baz.s(num))
    sub_chain_to_run.set(link=bif.s())
    return sub_chain_to_run

chain_to_run = chain()

job = reduce((lambda x, y: chain(x, y)), [make_chain(num) for num in range(3)])

job.apply_async()



