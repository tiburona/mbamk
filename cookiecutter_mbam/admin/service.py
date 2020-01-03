from .models import UserAdmin, RoleAdmin
from cookiecutter_mbam.user import User, Role
from cookiecutter_mbam.extensions import db

def init_admin(f_admin):
    f_admin.add_view(UserAdmin(User, db.session))
    f_admin.add_view(RoleAdmin(Role, db.session))