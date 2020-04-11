#!/usr/bin/env bash

echo "Downloading output from Freesurfer recon"

python3 download.py $1 $XNAT_USER $XNAT_PASS $3

echo "done downloading files"

cd /subjects/currsub

/usr/local/bin/run.sh currsub


echo "zipping up outputs"

cd /subjects/currsub

zip -r ./3d.zip ./3d

cd /usr/local/src

echo "uploading obj output"

python3 upload.py $2 $XNAT_USER $XNAT_PASS $3