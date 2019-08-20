import sys
import os
from .utils import init_session

experiment, user, password, host = sys.argv[1:]

url = os.path.join(host, 'data', 'experiments', experiment, 'resources/FSv6/files')

with init_session(user, password) as s:
    for z_name in ['stats.zip', 'surf.zip']:
        upload = {'file': (z_name, open('./' + z_name, 'rb'), 'application/octet-stream')}
        r = s.put(url + '?extract=true', files=upload)







