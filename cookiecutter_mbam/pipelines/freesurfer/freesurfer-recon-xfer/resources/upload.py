import sys
import os
import requests

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

experiment, user, password, host = sys.argv[1:]

url = os.path.join(host, 'data', 'experiments', experiment, 'resources/FSv6/files')

with init_session(user, password) as s:
    for z_name in ['stats.zip', 'surf.zip']:
        upload = {'file': (z_name, open('./' + z_name, 'rb'), 'application/octet-stream')}
        r = s.put(url + '?extract=true', files=upload)







