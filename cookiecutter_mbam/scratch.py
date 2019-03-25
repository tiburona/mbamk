




from celery import Celery, chain

app = Celery('scratch', backend='redis://localhost:6379', broker='redis://localhost:6379')


@app.task
def add(x, y):
    return x + y

@app.task
def subtract(x, y, z):
    return x - y - z

res = chain(add.s(4, 4) | subtract.s(1, 1)).apply_async()

res.wait()

print(res.result)
