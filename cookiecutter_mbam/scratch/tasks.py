from scratch import celery as cel

@cel.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def foo(self, a, b):
    return a + b

@cel.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def bar(self, c, d):
    return c + d

@cel.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def baz(self, e, f):
    return sum(e, f)

@cel.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def bif(self, g):
    return g


# @cel.task
# def foo(a, b):
#     return a + b
#
# @cel.task
# def bar(c, d):
#     return c + d
#
# @cel.task
# def baz(e, f):
#     return sum(e, f)



