from flask_security import utils
from flask_sqlalchemy import models_committed, before_models_committed
from .scan.models import Scan
from .experiment.models import Experiment
from datetime import date

def create_test_users(app, user_datastore, db):

    @app.before_first_request
    def before_first_request():

        db.create_all()

        user_datastore.find_or_create_role(name='admin', description='Administrator')
        user_datastore.find_or_create_role(name='end-user', description='End user')

        if not user_datastore.get_user('someone@example.com'):
            user_datastore.create_user(email='someone@example.com', password='password')
        if not user_datastore.get_user('admin@example.com'):
            user_datastore.create_user(email='admin@example.com', password='password')

        # Add scans to the first user
        Experiment.create(date=date.fromisoformat('2008-12-04'),
                         scanner=None,
                         field_strength=None,
                         user_id=1,
                         num_scans = 1,
                         xnat_id = 'MIND02_E00612',
                         xnat_label = '000001_MR1',
                         scan_counter = 1)

        Scan.create(xnat_status='Uploaded',
                    aws_status='Uploaded',
                    xnat_uri='/data/experiments/MIND02_E00612/scans/T1_01',
                    xnat_id='T1_01',
                    aws_key='user/1/experiment/1/scan/1/file/T1.nii.gz',
                    experiment_id=1,
                    user_id=1)

        Experiment.create(date=date.fromisoformat('2012-05-12'),
                         scanner=None,
                         field_strength=None,
                         user_id=1,
                         num_scans = 2,
                         xnat_id = 'MIND02_E00592',
                         xnat_label = '000001_MR2',
                         scan_counter = 2)

        Scan.create(xnat_status='Uploaded',
                    aws_status='Uploaded',
                    xnat_uri='/data/experiments/MIND02_E00592/scans/T1_01',
                    xnat_id='T1_01',
                    aws_key='user/1/experiment/2/scan/1/file/T1.nii.gz',
                    experiment_id=2,
                    user_id=1)

        Scan.create(xnat_status='Uploaded',
                    aws_status='Uploaded',
                    xnat_uri='/data/experiments/MIND02_E00592/scans/6',
                    xnat_id='6',
                    aws_key='user/1/experiment/2/scan/2/file/T1.nii.gz',
                    experiment_id=2,
                    user_id=1)

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
