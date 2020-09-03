from .models import Experiment
from cookiecutter_mbam.user import User
from cookiecutter_mbam.base.tasks import run_task_factories
from cookiecutter_mbam import celery as cel
from celery import group, chain
from cookiecutter_mbam.scan.tasks import get_scan_attribute
from cookiecutter_mbam.user.tasks import set_attributes as set_subject_attributes
from flask import url_for

set_attribute, set_attributes, get_attribute = run_task_factories(Experiment)


@cel.task
def set_experiment_attribute(*args):
    return set_attribute(*args)


@cel.task
def get_experiment_attribute(*args):
    return get_attribute(*args)


@cel.task
def set_experiment_attributes(*args):
    return set_attributes(*args)


@cel.task
def get_scan_xnat_ids(scan_ids):
    # The below was changed from group to chain because of a celery bug
    # See https://github.com/celery/celery/issues/1881
    return chain([get_scan_attribute.s('xnat_id', scan_id) for scan_id in scan_ids])()


@cel.task
def set_sub_and_exp_xnat_attrs(responses, xnat_labels, user_id, exp_id, attrs_to_set):
    attrs = {key: {
        'xnat_id': responses[key],
        'xnat_uri': '/data/{}s/{}'.format(key, responses[key]),
        'xnat_label': xnat_labels[key]['xnat_label']}
        for key in attrs_to_set}
    if 'subject' in attrs_to_set:
        set_subject_attributes(attrs['subject'], user_id)
    if 'experiment' in attrs_to_set:
        set_experiment_attributes(attrs['experiment'], exp_id)


def build_status_message(statuses, user):

    ordinal_words = ['first', 'second', 'third']

    responses = {
        'YAY': "scan was successfully uploaded to My Brain and Me! You can view your scans at {}".format(
            url_for('display.displays', _external=True)),

        'meh': "scan was uploaded to My Brain and Me, but something went wrong and you may not be able to view it yet. "
               "If you can not view it at {}, please feel free to email us at info@mybrainandme.org.".format(
            url_for('display.displays', _external=True)),

        'Boo': "scan was not uploaded to My Brain and Me because something went wrong. The admins have been notified. "
               "Please try again in a few minutes. If the problem persists, feel free to email us at "
               "info@mybrainandme.org."
    }

    scan_word = 'scans' if len(responses) > 1 else 'scan'

    message_text = '''Dear {},\nThank you for uploading your brain {} to My Brain and Me! '''.format(
        user.first_name, scan_word)

    for i, status in enumerate(statuses):
        message_text += "Your {} ".format(ordinal_words[i]) + responses[status] + '\n'

    return message_text


@cel.task
def construct_status_email(experiment_id):
    """ For a given experiment id, this returns email_info
    :param: experiment_id
    :return: tuple a three-tuple of the recipient's name and email address, as well as message, a dictionary
    with two keys, 'subject' and 'body' """

    experiment = Experiment.get_by_id(experiment_id)
    user = User.get_by_id(experiment.user_id)

    for scan in experiment.scans:
        statuses = []
        if scan.aws_status == 'Uploaded' and scan.xnat_status == 'Uploaded':
            statuses.append('YAY')
        elif scan.aws_status != 'Uploaded' and scan.xnat_status != 'Uploaded':
            statuses.append('Boo')
        else:
            statuses.append('meh')

    message = {'subject': 'Upload Status',
               'body': build_status_message(statuses, user)}

    return user.full_name, user.email, message
