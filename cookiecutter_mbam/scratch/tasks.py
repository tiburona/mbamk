from celery import Celery

cel = Celery(__name__,
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/1')

@cel.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def foo(self, a, b):
    return a + b

@cel.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def bar(self, c, d):
    return c + d

@cel.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def baz(self, e, f):
    print("I'm in baz")
    return e + f

@cel.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def bif(self, g):
    print(g)





