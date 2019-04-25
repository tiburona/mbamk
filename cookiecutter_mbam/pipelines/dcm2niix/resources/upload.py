import requests
import sys
import os
import gzip

url, user, password, host = sys.argv[1:]

def get_file_by_extension(dir, ext):
    return [file for file in os.listdir(dir) if os.path.splitext(file)[1] == ext][0]

nii_path = os.path.join('/output', get_file_by_extension('/output', '.nii'))
json_path = os.path.join('/output', get_file_by_extension('/output', '.json'))

gz_path = nii_path + '.gz'

with gzip.open(gz_path, 'wb') as gzipped_file:
    with open(nii_path, 'rb') as f:
        gzipped_file.writelines(f)

files = {'nii_file': ('T1.nii.gz', open(gz_path, 'rb'), 'application/octet-stream'),
         'json_file': ('T1_info.json', open(json_path, 'rb'), 'application / octet-stream')}

def init_session(user, password):
    s = requests.Session()
    s.auth = (user, password)
    return s

with init_session(user, password) as s:
    s.put(host + url)
    s.put(host + url, files=files)