from cookiecutter_mbam import celery
import ssl, smtplib
#from cookiecutter_mbam.settings import MAIL_PASSWORD
from cookiecutter_mbam.logger import file_handler, mail_handler
from celery.utils.log import get_task_logger
from cookiecutter_mbam.config import config_by_name, config_name

logger = get_task_logger(__name__)
logger.addHandler(file_handler)
logger.addHandler(mail_handler)

# Set mail password 
MAIL_PASSWORD=config_by_name[config_name].MAIL_PASSWORD

messages = {
    'generic_message': "An error occurred",
    'user_upload_message': "Something went wrong uploading your scan.",
    'user_external_uploads': "Your scan was uploaded to our site, but something went wrong with the services we use to " \
                             "process it, so it won't be visible until we fix it.  The admins have been notified."

}

def setter_factory(cls):
    def set_attribute(val, instance_id, key):
        instance = cls.get_by_id(instance_id)
        args = {key: val}
        instance.update(**args)
        return val
    return set_attribute

def getter_factory(cls):
    def get_attribute(key, instance_id):
        return getattr(cls.get_by_id(instance_id), key)
    return get_attribute

def multi_setter_factory(cls):
    def set_attributes(attr_dict, instance_id):
        instance = cls.get_by_id(instance_id)
        for key, val in attr_dict.items():
            instance.update(**{key: val})
        return attr_dict
    return set_attributes

def run_task_factories(cls):
    return setter_factory(cls), multi_setter_factory(cls), getter_factory(cls)

@celery.task
def send_email(email_info):
    user_name, user_email, message = email_info
    port = 587
    smtp_server = "smtp.gmail.com"
    sender_email = "testingmbam@gmail.com"
    recipient = f'{user_name} <{user_email}>'
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, MAIL_PASSWORD)
        server.sendmail(sender_email, recipient, message)
    return

@celery.task
def global_error_handler(req, exc, tb, log_message='generic_message', user_name='', user_email='',
                         user_message='generic_message', email_user=True, email_admin=False):
    if email_user:
        email_info = (user_name, user_email, messages[user_message])
        send_email.s(email_info).apply_async()
    logger.error(messages[log_message], exc_info=True, extra={'email_admin': email_admin})
