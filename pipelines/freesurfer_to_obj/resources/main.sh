#!/usr/bin/env bash

echo "Downloading output from Freesurfer recon"

python3 download.py $1 $XNAT_USER $XNAT_PASS $3

echo "done downloading files"

/usr/local/bin/run.sh /input


echo "zipping up outputs"
pushd /subjects/currsub/
zip -r $(popd)/3d.zip ./3d/
popd

echo "uploading obj output"

python3 upload.py $2 $XNAT_USER $XNAT_PASS $3