#!/usr/bin/env bash

echo "downloading structural NIFTI files"

python3 download.py $1 $XNAT_USER $XNAT_PASS $XNAT_HOST

echo "starting freesurfer recon"

recon-all -i /input/T1.nii.gz -subject currsub -all

echo "uploading recon output"


# todo: make this so that it can pull multiple scans from an experiment
# $1 is the URL of the experiment
python3 upload.py $1 $XNAT_USER $XNAT_PASS $XNAT_HOST

