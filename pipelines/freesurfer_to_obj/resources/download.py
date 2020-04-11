import requests
import sys
import os

url, user, password, host = sys.argv[1:]

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

with init_session(user, password) as s:
    r = s.get(url)
    for file in r.json()['ResultSet']['Result']:
        if 'json' not in file['Name']:
            r = s.get(host + file['URI'])
            if r.status_code == 200:
                for subdir in ['stats/', 'mri/', 'surf/', 'scripts/', 'label/', 'touch/']:
                    if subdir in file['URI']:
                        with open('/subjects/currsub/' + subdir + file['Name'], 'wb') as f:
                            f.write(r.content)