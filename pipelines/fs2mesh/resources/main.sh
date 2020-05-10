#!/usr/bin/env bash

echo "Downloading output from Freesurfer recon"

python3 download.py $1 $XNAT_USER $XNAT_PASS $3

echo "done downloading files"

cd /subjects/currsub

/opt/fs2mesh/run.sh currsub

echo "zipping up outputs"

cd /subjects/currsub

zip -r ./mesh.zip ./mesh

cd /usr/local/src

echo "uploading mesh output"

python3 upload.py $2 $XNAT_USER $XNAT_PASS $3