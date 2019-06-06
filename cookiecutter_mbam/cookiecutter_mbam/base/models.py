from .tasks import global_error_handler
from flask import request
from flask_security import current_user
import traceback
from functools import reduce
from celery import chain


from flask import current_app

def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

class BaseService():
    def __init__(self, cls=None, tasks={}):
        self.cls = cls
        self.tasks = tasks

    #todo: think about appropriateness of property decorator here
    def _username(self):
        try:
            return current_user.name
        except:
            return ''

    def _error_handler(self, log_message, user_message=''):
        return global_error_handler.s(log_message=log_message, user_name=self._username(),
                                      user_email=current_user.email, user_message=user_message,  email_user=True,
                                      email_admin=False)

    def _call_error_handler(self, exc, log_message, user_message=''):
        global_error_handler(request, exc, traceback.format_exc(), log_message=log_message, user_name=self._username(),
                             user_email=current_user.email, user_message=user_message, email_user=True,
                             email_admin=False)

    def set_attribute(self, instance_id, key, val='', passed_val=False):
        return self._gen_signature_of_factory_task('set_attribute', val, instance_id, key, passed_val=passed_val)

    def get_attribute(self, instance_id, attr='', passed_val=False):
        return self._gen_signature_of_factory_task('get_attribute', attr, instance_id, passed_val=passed_val)

    def set_attributes(self, instance_id, attributes={}, passed_val=False):
        if not passed_val:
            return reduce(chain, [self._gen_signature_of_factory_task('set_attribute', val, instance_id, key)
                                  for key, val in attributes.items()])
        else:
            return self._gen_signature_of_factory_task('set_attributes', attributes, instance_id, passed_val=passed_val)

    def _gen_signature_of_factory_task(self, task_key, optional_arg, *args, passed_val=False):
        try:
            task = self.tasks[task_key]
            if passed_val:
                return task.s(*args)
            else:
                return task.si(optional_arg, *args)
        except KeyError:
            # todo: do something
            pass
        except:
            pass
