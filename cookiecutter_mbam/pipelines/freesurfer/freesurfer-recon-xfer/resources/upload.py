import sys
import os
import requests

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

project, subject, experiment, user, password, host = sys.argv[1:]

url = os.path.join(host, 'data', 'projects', project, 'subjects', subject, 'experiments', experiment, 'resources/FSv6/files')

print(url)

with init_session(user, password) as s:
    for z_name in ['stats.zip', 'surf.zip','mri.zip']:
        upload = {'file': (z_name, open('./' + z_name, 'rb'), 'application/octet-stream')}
        r = s.put(url + '?extract=true', files=upload)







