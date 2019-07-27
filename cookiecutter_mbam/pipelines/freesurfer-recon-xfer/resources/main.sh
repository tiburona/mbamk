#!/usr/bin/env bash

echo "downloading structural NIFTI files"
#
experiment=$1
inputScansArray=$2

for i in "${inputScansArray[@]}"
do
   python3 download.py $1 $i $XNAT_USER $XNAT_PASS $XNAT_HOST
done

echo "done downloading files"

# I need to figure out how to deal with optional args with bash
args=()

for i in /input/*
do
    filename="$(basename -- "$i")"
    args=( "${args[@]}" "-i" )
    args=( "${args[@]}" "/input/$filename" )
done


args+=("-s")
args+=("currsub")
args+=("-all")

echo ${args[@]}

echo "starting freesurfer recon"

recon-all "${args[@]}"

echo "uploading recon output"

# $1 is the URL of the experiment
python3 upload.py $experiment $XNAT_USER $XNAT_PASS $XNAT_HOST

