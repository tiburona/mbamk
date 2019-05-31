from .models import User
from cookiecutter_mbam.base_service import BaseService
from .tasks import set_user_attribute, get_user_attribute

tasks = {'set_attribute': set_user_attribute, 'get_attribute': get_user_attribute}

class UserService(BaseService):

    def __init__(self, tasks=tasks):
        super().__init__(User)
        self.tasks = tasks
