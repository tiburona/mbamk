import logging
import sys
from logging.handlers import SMTPHandler
from logging import FileHandler
from flask import request
from celery.app.log import TaskFormatter
from celery.utils.log import get_task_logger
from cookiecutter_mbam.config import Config as config

app_logger = logging.getLogger()
celery_logger = get_task_logger(__name__)

# todo: figure out why this request.url etc. appears as an unhandled error in wsgi logging.
# It doesn't seem to effect anything but is confusing noise.


class TlsSMTPHandler(SMTPHandler):
    """adapted from http://mynthon.net/howto/-/python/python%20-%20logging.SMTPHandler-how-to-use-gmail-smtp-server.txt"""
    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                self.fromaddr,
                ",".join(self.toaddrs),
                self.getSubject(record),
                formatdate(), msg)
            if self.username:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

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
        try:
            return rec.email_admin
        except:
            return False

mail_handler = TlsSMTPHandler(
    mailhost='smtp.gmail.com',
    fromaddr=config.SECURITY_EMAIL_SENDER,
    toaddrs=['tiburona@gmail.com'],
    subject='Application Error',
    credentials=(config.MAIL_USERNAME, config.MAIL_PASSWORD)
)

mail_handler.addFilter(MailFilter())
file_handler = FileHandler('./mbam.log')
stream_handler = logging.StreamHandler(sys.stdout)

for handler in [mail_handler, file_handler, stream_handler]:
    handler.setFormatter(request_and_task_formatter)
    if handler in [mail_handler, file_handler]:
        handler.setLevel(logging.ERROR)
    else:
        handler.setLevel(logging.INFO)

for logger in [app_logger, celery_logger]:
    for handler in [mail_handler, file_handler]:
        logger.addHandler(handler)
