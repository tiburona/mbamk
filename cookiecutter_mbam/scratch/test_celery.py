from scratch import celery as cel

@cel.task
def foo(a, b):
    return a + b

@cel.task
def bar(c, d):
    return c + d

@cel.task
def baz(e, f):
    return sum(e, f)

