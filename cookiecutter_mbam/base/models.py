from .tasks import global_error_handler, trigger_job, zipdir, send_email
from flask import request
from flask_security import current_user
import traceback
from functools import reduce
from celery import chain
from cookiecutter_mbam.config import Config


class BaseModel:

    def _error_handler(self, log_message, user_message='', email_admin=True, email_user=True):
        """Generates the signature of a `global_error_handler`, a Celery task to handle errors

        `on_error` Celery tasks are passed the request, the exception, and the traceback as the implicit first three
        arguments.
        """
        return global_error_handler.s(cel=True, log_message=log_message, user_name=self.username,
                                      user_email=current_user.email, user_message=user_message,  email_user=email_user,
                                      email_admin=email_admin)

    def _call_error_handler(self, exc, log_message, user_message='', email_admin=True, email_user=True):
        """Call `global_error_handler` as a function, not as a Celery task.

        Example usage:

        def add_a_scan(self, experiment_id):
            try:
                Scan.create(experiment_id=experiment_id)
            except Exception as e:
                self._call_error_handler(e, "There was an error")
        """
        global_error_handler(request, exc, traceback.format_exc(), cel=False, log_message=log_message,
                             user_name=self._username(), user_email=current_user.email, user_message=user_message,
                             email_user=email_user, email_admin=email_admin)

    @property
    def username(self):
        return self._username()

    def _username(self):
        try:
            return current_user.full_name
        except (NameError, AttributeError) as e:
            self._call_error_handler(e, "Received error in setting username property", email_user=False)
            return ''


class BaseService(BaseModel):

    def __init__(self, cls=None, tasks={}):
        self.cls = cls
        self.tasks = tasks

    @staticmethod
    def _trigger_job(job, passed_val=False, *args, **kwargs):
        if passed_val:
            return trigger_job.s(job)
        else:
            return trigger_job.si(job, *args, **kwargs)

    def zipdir(self, dir_to_zip, dest_dir, name=''):
        return zipdir.si(dir_to_zip, dest_dir, name=name)

    def set_attribute(self, instance_id, key, val='', passed_val=False):
        return self._gen_signature_of_factory_task('set_attribute', val, instance_id, key, passed_val=passed_val)

    def get_attribute(self, instance_id, attr='', passed_val=False):
        return self._gen_signature_of_factory_task('get_attribute', attr, instance_id, passed_val=passed_val)

    def set_attributes(self, instance_id, attributes={}, passed_val=False):

        if not passed_val:
            return reduce(chain, [self._gen_signature_of_factory_task('set_attributes', val, instance_id, key)
                                  for key, val in attributes.items()])
        else:
            return self._gen_signature_of_factory_task('set_attributes', attributes, instance_id, passed_val=passed_val)

    def _gen_signature_of_factory_task(self, task_key, optional_arg, *args, passed_val=False):
        task = self.tasks[task_key]
        if passed_val:
            return task.s(*args)
        else:
            return task.si(optional_arg, *args)

    @staticmethod
    def _send_email():
        # todo put in if statement allowing this to be immutable
        return send_email.s()

    def _set_config(self, config_vars):
        [setattr(self, attr, getattr(Config, config_var)) for attr, config_var in config_vars]
