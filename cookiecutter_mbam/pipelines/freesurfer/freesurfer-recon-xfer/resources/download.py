import requests
import sys
import os

project, subject, experiment, scan, user, password, host = sys.argv[1:]

url = os.path.join(host, 'data', 'projects', project, 'subjects', subject, 'experiments', experiment, 'scans', scan, 'resources', 'NIFTI', 'files')

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

with init_session(user, password) as s:
    r = s.get(url)
    for file in r.json()['ResultSet']['Result']:
        r = s.get(host + file['URI'])
        if r.status_code == 200:
            with open('/input/' + file['Name'], 'wb') as f:
                f.write(r.content)




