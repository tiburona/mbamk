import os
import zipfile
from .models import Scan
from cookiecutter_mbam.user import User
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery as cel
from flask import url_for

set_attribute, set_attributes, get_attribute = run_task_factories(Scan)

@cel.task
def set_scan_attribute(*args):
    return set_attribute(*args)

@cel.task
def get_scan_attribute(*args):
    return get_attribute(*args)

@cel.task
def set_scan_attributes(*args):
    return set_attributes(*args)

@cel.task
def construct_mesh_status_email(scan_id):
    scan = Scan.get_by_id(scan_id)
    fs2mesh = [d for d in scan.derivations if d.process_name == 'fs_to_mesh'][0]
    user = User.get_by_id(scan.user_id)

    greeting = "Dear {},\n".format(user.first_name)

    if fs2mesh.aws_status == 'Uploaded':
        body = "A 3D view of your scan was successfully generated! You can view your scans at {}".format(
             url_for('display.displays', _external=True))
    else:
        body = "Something went wrong and My Brain and Me was not able to generate a 3D image of your scan.  The " \
                  "admins have been notified but if you don't hear from us feel free to email us at goodluck@chump.com."

    body = greeting + body

    message = {
        'subject': 'Scan Status',
        'body': body
    }

    return user.full_name, user.email, message














