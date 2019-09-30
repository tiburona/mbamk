#!/usr/bin/env bash

echo "downloading structural NIFTI files"


project=$1
shift
subject=$1
shift
experiment=$1
shift

for i
do
   python3 download.py $project $subject $experiment $i $XNAT_USER $XNAT_PASS $XNAT_HOST
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


echo "zipping up outputs"
zip -r stats.zip /output/currsub/stats/
zip -r surf.zip /output/currsub/surf/

echo "uploading recon output"

python3 upload.py $project $subject $experiment $XNAT_USER $XNAT_PASS $XNAT_HOST

