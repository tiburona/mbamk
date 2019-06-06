import logging
from logging.handlers import SMTPHandler
from logging import FileHandler
from flask import request
from celery.app.log import TaskFormatter

logger = logging.getLogger()

# todo: figure out why this request.url etc. appears as an unhandled error in wsgi logging.
# It doesn't seem to effect anything but is confusing noise.

class RequestandTaskFormatter(TaskFormatter):
    def format(self, record):
        try:
            record.url = request.url
            record.remote_addr = request.remote_addr
        except (RuntimeError, KeyError):
            record.url = '???'
            record.remote_addr = '???'
        return super().format(record)

request_and_task_formatter = RequestandTaskFormatter(
    '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
     '%(task_id)s - %(task_name)s - %(name)s\n'
    '%(levelname)s in %(module)s: %(message)s'
)

class MailFilter(logging.Filter):
    def filter(self, rec):
        return rec.email_admin

mail_handler = SMTPHandler(
    mailhost='smtp.gmail.com',
    fromaddr='testingmbam@gmail.com',
    toaddrs=['testingmbam@gmail.com'],
    subject='Application Error'
)
mail_handler.addFilter(MailFilter())
mail_handler.setFormatter(request_and_task_formatter)
mail_handler.setLevel(logging.ERROR)

file_handler = FileHandler('/Users/katie/mbam.log')
file_handler.setFormatter(request_and_task_formatter)
file_handler.setLevel(logging.ERROR)

logger.addHandler(mail_handler)
logger.addHandler(file_handler)



