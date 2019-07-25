import requests
import sys
import os

url, user, password, host = sys.argv[1:]



url = os.path.join(host + url, 'resources', 'DICOM', 'files')

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




