#!/usr/bin/env bash

echo "downloading DICOMS"

python3 download.py $1 $XNAT_USER $XNAT_PASS $XNAT_HOST

echo "converting DICOMS"

dcm2niix -o /output /input

echo "uploading DICOMS"

python3 upload.py $1 $XNAT_USER $XNAT_PASS $XNAT_HOST

