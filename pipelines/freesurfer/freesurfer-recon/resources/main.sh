#!/usr/bin/env bash

echo "downloading structural NIFTI files"

python3 download.py $1 $XNAT_USER $XNAT_PASS $3

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
args+=("-parallel")

echo "starting freesurfer recon with args:"
echo ${args[@]}

recon-all "${args[@]}"


echo "zipping up outputs"

pushd /output/currsub

for SUBDIR in label mri scripts stats surf touch
do
	zip -r "./$SUBDIR.zip" "./$SUBDIR"
done

popd

echo "uploading recon output"

python3 upload.py $2 $XNAT_USER $XNAT_PASS $3


