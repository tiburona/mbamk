import pyxnat
import collections

xnat = pyxnat.Interface(config="/home/ubuntu/workspace/flask_brain_db/mind-xnat.cfg")
seed_projects=['IXI'] # Here will add additional projects
user_project=['MBAM_TEST']

def get_db_counts():
    # Here get seed data counts
    seed_count=0
    for PROJECT in seed_projects:
        subs=xnat.select.projects(PROJECT).subjects('*').get()
        seed_count=seed_count+len(subs)
    
    # Here get user counts    
    subs=xnat.select.projects('MBAM_TEST').subjects('*').get()
    user_count=len(subs)
    Counts = collections.namedtuple('Counts', ['seed', 'user'])
    my_count=Counts(seed=str(seed_count).zfill(4),user=str(user_count).zfill(4))
    return my_count