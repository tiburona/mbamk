from flask_sqlalchemy import event
from flask_security import current_user

def resource_belongs_to_user(resource_type, instance_id):
    """ Verify that what the user wants to view belongs to the user
    :param resource_type class:  The Class (i.e Scan, Derivation, Experiment)
    :param instance_id int: The id of the resource
    :return: Boolean
     """
    if resource_type.get_by_id(instance_id):
        return resource_type.get_by_id(instance_id).user_id == current_user.id
    return False

#todo: add counter incrementing to this!
def make_ins_del_listener(child_model, parent_model, child_model_str, parent_model_str,
                                      event_type, inc_quant):


    @event.listens_for(child_model, event_type)
    def listener(mapper, connection, target):
        parent_id = getattr(target, parent_model_str + '_id')
        parent = parent_model.get_by_id(parent_id)
        num_attr_name = 'num_' + child_model_str + 's'
        num = getattr(parent, num_attr_name) + inc_quant
        print(num)
        table = parent_model.__table__
        connection.execute(
            table
                .update()
                .where(table.c.id == parent_id)
                .values(**{num_attr_name:num})
        )

    return listener




    #
    # @event.listens_for(Scan, "after_insert")
    # def after_insert_listener(mapper, connection, target):
    #     experiment = Experiment.get_by_id(target.experiment_id)
    #     num_scans = experiment.num_scans + 1
    #     experiment_table = Experiment.__table__
    #     connection.execute(
    #         experiment_table
    #             .update()
    #             .where(experiment_table.c.id == target.experiment_id)
    #             .values(num_scans=num_scans)
    #     )
