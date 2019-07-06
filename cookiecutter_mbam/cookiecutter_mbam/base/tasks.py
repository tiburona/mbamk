from cookiecutter_mbam import celery
import ssl
import smtplib
from email.message import EmailMessage
from cookiecutter_mbam.logger import file_handler, mail_handler
from celery.utils.log import get_task_logger
from cookiecutter_mbam.config import config_by_name, config_name
from . import textbank

logger = get_task_logger(__name__)
logger.addHandler(file_handler)
#logger.addHandler(mail_handler)

# set mail constants
mail_constants = ['USERNAME', 'SERVER', 'PASSWORD', 'PORT']
UNAME, SERVER, PASSWORD, PORT = [getattr(config_by_name[config_name], 'MAIL_'+ const) for const in mail_constants]


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

@celery.task
def send_email(email_info):
    user_name, user_email, message = email_info
    recipient = f'{user_name} <{user_email}>'
    message = format_email(message, UNAME, recipient)
    context = ssl.create_default_context()
    with smtplib.SMTP(SERVER, PORT) as server:
        server.starttls(context=context)
        server.login(UNAME, PASSWORD)
        server.send_message(message)
    return

def format_email(message, sender_email, recipient):
    msg = EmailMessage()
    msg.set_content(message['body'])
    msg['Subject'] = message['subject']
    msg['To'] = recipient
    msg['From'] = sender_email
    return msg


@celery.task
def global_error_handler(req, exc, tb, log_message='generic_message', user_name='', user_email='',
                         user_message='generic_message', email_user=True, email_admin=False):
    if email_user:
        email_info = (user_name, user_email, textbank.messages[user_message])
        send_email.s(email_info).apply_async()
    logger.error(textbank.messages[log_message]['subject'], exc_info=True, extra={'email_admin': email_admin})
