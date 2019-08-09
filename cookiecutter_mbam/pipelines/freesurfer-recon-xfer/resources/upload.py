import requests
import sys
import os
from glob import glob
import zipfile

surf_names = ['surf/?h.pial', 'surf/?h.sphere.reg', 'surf/?h.thickness', 'surf/?h.volume', 'surf/?h.area', 'surf/?h.sulc',
    'surf/?h.curv', 'surf/?h.avg_curv']

surf_files = []

os.chdir('/output/currsub/')

for name in surf_names:
    surf_files.extend(glob('./' + name))

stats_files = glob('./stats/*')

znames_files = [('surf.zip', surf_files), ('stats.zip', stats_files)]

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

experiment, user, password, host = sys.argv[1:]

url = os.path.join(host, 'data', 'experiments', experiment, 'resources/FSv6/files')

with init_session(user, password) as s:
    for z_name, files in znames_files:
        with zipfile.ZipFile(z_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                zf.write(file)
        files = {'file': (z_name, open('./' + z_name, 'rb'), 'application/octet-stream')}
        r = s.put(url + '?extract=true', files=files)







