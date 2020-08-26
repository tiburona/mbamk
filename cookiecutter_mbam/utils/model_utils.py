from flask_sqlalchemy import event
from flask_security import current_user
from datetime import datetime


# Todo: Turn this into a wrapper function that wraps the @app.route like @login_required?
def resource_belongs_to_user(resource_type, instance_id):
    """ Verify that what the user wants to view belongs to the user
    :param resource_type class:  The Class (i.e Scan, Derivation, Experiment)
    :param instance_id int: The id of the resource
    :return: Boolean
     """
    if resource_type.get_by_id(instance_id):
        return resource_type.get_by_id(instance_id).user_id == current_user.id
    return False

def make_insert_listener(child_model, parent_model, child_model_str, parent_model_str):
    @event.listens_for(child_model, 'after_insert')
    def listener(mapper, connection, target):
        parent_id = getattr(target, parent_model_str + '_id')
        parent = parent_model.get_by_id(parent_id)
        counter_attr_name = child_model_str + '_counter'
        counter = getattr(parent, counter_attr_name)
        table = parent_model.__table__
        connection.execute(
            table
            .update()
            .where(table.c.id == parent_id)
            .values(**{counter_attr_name: counter + 1})
        )
    return listener


def date_validator(start_date, date, end_date=datetime.today().date()):
    if not start_date < date <= end_date:
        raise AssertionError('Invalid date')
    return date


def status_validator(status, key, allowed):
    if not status in allowed:
        raise AssertionError("Invalid {}: {}".format(key, status))
    return status

