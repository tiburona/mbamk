#!/usr/bin/env bash

echo "downloading DICOMS"

python3 download.py $1 $XNAT_USER $XNAT_PASS $3

echo "converting DICOMS"

dcm2niix -o /output /input

echo "uploading NIFTI"

python3 upload.py $2 $XNAT_USER $XNAT_PASS $3

