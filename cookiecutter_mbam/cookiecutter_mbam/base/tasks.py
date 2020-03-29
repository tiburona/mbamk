from celery.signals import after_setup_logger, after_setup_task_logger
import json
import zipfile
import os
from celery import signature
from cookiecutter_mbam import celery as cel
import ssl
import smtplib
from email.message import EmailMessage
from cookiecutter_mbam.config import config_by_name, config_name
from . import textbank
from cookiecutter_mbam.mbam_logging import app_logger, celery_logger

# set mail constants
mail_constants = ['MAIL_USERNAME', 'MAIL_SERVER', 'MAIL_PASSWORD', 'MAIL_PORT','SECURITY_EMAIL_SENDER']
UNAME, SERVER, PASSWORD, PORT, SENDER = [getattr(config_by_name[config_name], const) for const in mail_constants]


# The following three functions are factory functions.  They generate setter and getter functions for the provided model
# class.  These functions will be converted into Celery tasks, so they can't take model objects as arguments directly;
# model objects are non-serializable.  To avoid needing to define the same functions over and over again for each model
# class, these factories are provided, and only the function run_task_factories needs to be executed for every class.

# For all these functions, the order of the arguments is important; when converted into Celery functions they will
# sometimes accept their first argument from a function executed before them in a chain.

def setter_factory(cls):
    """ Generate the setter function for the given Model

    :param Model cls: the class of the object on which the attribute will be set (e.g. Scan, Derivation)
    :return: a function that can take a key/val pair and the id of the model instance and set the 'key' attribute on the
    instance equal to the val
    :rtype: function
    """
    def set_attribute(val, instance_id, key):
        instance = cls.get_by_id(instance_id)
        args = {key: val}
        instance.update(**args)
        return val
    return set_attribute

def getter_factory(cls):
    """ Generate the getter function for the given Model

    :param Model cls: the class of the object from which the attribute will be gotten (e.g. Scan, Derivation)
    :return: a function that can take a key and the id of the model instance and get the value of the attribute
    indicated by the key
    :rtype: function
    """
    def get_attribute(key, instance_id):
        return getattr(cls.get_by_id(instance_id), key)
    return get_attribute

def multi_setter_factory(cls):
    """ Generate a function for the given Model to set multiple attributes on an instance

    :param Model cls: the class of the object on which the attribute will be set (e.g. Scan, Derivation)
    :return: a function that can take a dictionary of attributes and their values, as well as the id of the model
    instance, and set each attribute.
    :rtype: function
    """
    def set_attributes(attr_dict, instance_id):
        instance = cls.get_by_id(instance_id)
        for key, val in attr_dict.items():
            instance.update(**{key: val})
        return attr_dict
    return set_attributes

def run_task_factories(cls):
    """ Generate the setter and getter functions for a given model object

    :param Model cls: the class of the object on which the returned functions will act
    :return tuple: a three-tuple of the functions, the setter, multi_setter, and getter functions
    :rtype: tuple
    """
    return setter_factory(cls), multi_setter_factory(cls), getter_factory(cls)

@cel.task
def send_email(email_info):
    """ Send an email

    :param tuple email_info: a three-tuple of the recipient's name and email address, as well as message, a dictionary
    with two keys, 'subject' and 'body'
    :return:
    """
    context = ssl.create_default_context()
    user_name, user_email, message = email_info

    msg = EmailMessage()
    msg.set_content(message['body'])
    msg['Subject'] = message['subject']
    msg['To'] = f'{user_name} <{user_email}>'
    msg['From'] = SENDER

    with smtplib.SMTP(SERVER, PORT) as server:
        server.starttls(context=context)
        server.login(UNAME, PASSWORD)
        server.send_message(msg)
    return

def format_email(sender_email, email_info):
    """ Format an email message

    :param str sender_email: the email of the sender
    :param tuple email_info: a three-tuple of the recipient's name and email address, as well as message, a dictionary
    with two keys, 'subject' and 'body'
    :return: msg
    :rtype: EmailMessage
    """
    user_name, user_email, message = email_info
    msg = EmailMessage()
    msg.set_content(message['body'])
    msg['Subject'] = message['subject']
    msg['To'] = f'{user_name} <{user_email}>'
    msg['From'] = sender_email
    return msg


@cel.task
def global_error_handler(req, exc, tb, cel, log_message='generic_message', user_name='', user_email='',
                         user_message='generic_message', email_user=True, email_admin=False):
    """
    :param Request req: with the following two parameters, arguments that are automatically passed to Celery error
    handlers, and so must be included, even though they are not used
    :param Exception exc: the second argument automatically passed to Celery error handlers
    :param Traceback tb: the third argument automatically passed to Celery error handlers
    :param bool cel: whether to send the message to the celery logger (as opposed to the main app logger)
    :param str log_message: a key in a dictionary that contains various log messages for different circumstances
    :param str user_name: the name of the current user
    :param str user_email: the email of the current user
    :param str user_message: a key in a dictionary that contains various messages to the user for different circumstances
    :param bool email_user: whether to email the user about the error
    :param bool email_admin: whether to email admins about the error
    :return: None
    """
    logger = celery_logger if cel else app_logger

    if email_user:
        email_info = (user_name, user_email, textbank.messages[user_message])
        send_email.s(email_info).apply_async()
    logger.error(textbank.messages[log_message]['subject'], exc_info=True, extra={'email_admin': email_admin})


@cel.task
def trigger_job(serialized_job, *args, **kwargs):
    canvas = signature(json.loads(serialized_job))
    canvas.apply_async(*args, **kwargs)

@cel.task
def zipdir(dir_to_zip, dest_dir, name='file.zip'):
    path = os.path.join(dest_dir, name)
    with zipfile.ZipFile(os.path.join(dest_dir, name), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dir_to_zip):
            for file in files:
                zipf.write(os.path.join(root, file))
    return path, name
