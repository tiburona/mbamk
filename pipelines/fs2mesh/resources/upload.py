import sys
import requests

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

url, user, password, host = sys.argv[1:]

with init_session(user, password) as s:
    upload = {'file': ('mesh.zip', open('/subjects/currsub/mesh.zip', 'rb'), 'application/octet-stream')}
    r = s.put(url + '?extract=true', files=upload)