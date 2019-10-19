import os
import glob
import zipfile

surf_names = ['surf/?h.pial', 'surf/?h.sphere.reg', 'surf/?h.thickness', 'surf/?h.volume', 'surf/?h.area', 'surf/?h.sulc',
    'surf/?h.curv', 'surf/?h.avg_curv']

surf_files = []

os.chdir('/output/currsub/')

for name in surf_names:
    surf_files.extend(glob('./' + name))

stats_files = glob('./stats/*')

znames_files = [('surf.zip', surf_files), ('stats.zip', stats_files)]

for z_name, files in znames_files:
    with zipfile.ZipFile(z_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            zf.write(file)