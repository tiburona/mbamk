from .models import UserAdmin, GenericAdmin
from .views import EmailView
from cookiecutter_mbam.user import User, Role
from cookiecutter_mbam.scan import Scan
from cookiecutter_mbam.experiment import Experiment
from cookiecutter_mbam.derivation import Derivation
from cookiecutter_mbam.extensions import db
from flask_admin.contrib.sqla import ModelView

def register_admin_views(admin):
    admin.add_view(UserAdmin(User, db.session, endpoint='users'))
    admin.add_view(GenericAdmin(Role, db.session))
    admin.add_view(GenericAdmin(Scan, db.session, endpoint='scans'))
    admin.add_view(GenericAdmin(Experiment, db.session, endpoint='experiments'))
    admin.add_view(GenericAdmin(Derivation, db.session, endpoint='derivations'))
    admin.add_view(EmailView(name='Send Email', endpoint='email'))
