from flask_security import utils
from flask_sqlalchemy import models_committed, before_models_committed

def create_test_users(app, user_datastore, db):

    @app.before_first_request
    def before_first_request():

        db.create_all()

        user_datastore.find_or_create_role(name='admin', description='Administrator')
        user_datastore.find_or_create_role(name='end-user', description='End user')

        encrypted_password = utils.hash_password('password')
        if not user_datastore.get_user('someone@example.com'):
            user_datastore.create_user(email='someone@example.com', password=encrypted_password)
        if not user_datastore.get_user('admin@example.com'):
            user_datastore.create_user(email='admin@example.com', password=encrypted_password)

        db.session.commit()

        user_datastore.add_role_to_user('someone@example.com', 'end-user')
        user_datastore.add_role_to_user('admin@example.com', 'admin')
        db.session.commit()

def models_committed_hooks(app):

    @models_committed.connect_via(app)
    def on_models_committed(sender, changes):
        for obj, change in changes:
            if change == 'delete' and hasattr(obj, '__after_delete__'):
                obj.__after_delete__()
            elif change == 'update' and hasattr(obj, '__after_update__'):
                obj.__after_update__()
            elif change == 'insert' and hasattr(obj, '__after_insert__'):
                obj.__after_insert__()
