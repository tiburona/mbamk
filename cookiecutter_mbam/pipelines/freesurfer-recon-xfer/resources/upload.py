import requests
import sys
import os
import gzip
from glob import glob

files_to_upload=[]

names = ['surf/?h.pial', 'surf/?h.sphere.reg', 'surf/?h.thickness', 'surf/?h.volume', 'surf/?h.area', 'surf/?h.sulc',
    'surf/?h.curv', 'surf/?h.avg_curv', 'stats/*']

for name in names:
    files_to_upload.extend(glob('/output/currsub/' + name))

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

experiment, user, password, host = sys.argv[1:]

urls = [os.path.join(host, 'data', 'experiments', experiment, path) for path in
        ['resources', 'resources/FSv6', 'resources/FSv6/files']]

with init_session(user, password) as s:
    for url in urls:
        s.put(url)

fs_path = '/output/currsub'


for file_path in files_to_upload:
    files = {'file': (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream')}
    with init_session(user, password) as s:
        s.put(urls[2], files=files)




