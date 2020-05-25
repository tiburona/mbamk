import sys
import os
import requests

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

url, user, password, host = sys.argv[1:]

print(url)

with init_session(user, password) as s:
    for z_name in ['stats.zip', 'surf.zip','mri.zip', 'scripts.zip', 'touch.zip', 'label.zip']:
        upload = {'file': (z_name, open('/output/currsub/' + z_name, 'rb'), 'application/octet-stream')}
        r = s.put(url + '?extract=true', files=upload)






