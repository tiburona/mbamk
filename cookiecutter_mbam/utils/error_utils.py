from flask import flash
from datetime import datetime


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)

def date_validator(start_date, date, end_date=datetime.today()):
    if not start_date < date <= end_date:
        raise AssertionError('invalid date')
    return date
