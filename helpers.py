from flask_brain_db import db, app
from urlparse import urlparse

# Below functions to help set foreign keys across two databases
def create_fk(column, schema=None, **kwargs):
    if schema:
        column = "%s.%s" % (schema, column)
    return db.ForeignKey(column, **kwargs)

def _find_schema(cls):
    if hasattr(cls, '__bind_key__'):
        binds = app.config.get('SQLALCHEMY_BINDS')
        bind = binds.get(cls.__bind_key__)
    else:
        bind = app.config.get('SQLALCHEMY_DATABASE_URI')
    return urlparse(bind).path.strip('/')