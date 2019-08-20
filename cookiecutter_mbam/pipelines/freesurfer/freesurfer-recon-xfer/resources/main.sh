#!/usr/bin/env bash

echo "downloading structural NIFTI files"

experiment=$1
shift
for i
do
   python3 download.py $experiment $i $XNAT_USER $XNAT_PASS $XNAT_HOST
done

echo "done downloading files"

args=()

for i in /input/*
do
    filename="$(basename -- "$i")"
    args+=( "-i")
    args+=("/input/$filename")
done

args+=("-s")
args+=("currsub")
args+=("-all")

echo "starting freesurfer recon with args:"
echo ${args[@]}

recon-all "${args[@]}"

echo "uploading recon output"

python3 upload.py $experiment $XNAT_USER $XNAT_PASS $XNAT_HOST

