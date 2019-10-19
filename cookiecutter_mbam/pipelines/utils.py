import requests

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s
