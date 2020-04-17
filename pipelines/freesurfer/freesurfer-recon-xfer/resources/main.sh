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
pushd /output/currsub/
zip -r $(popd)/stats.zip ./stats/
zip -r $(popd)/mri.zip ./mri/aseg.mgz
zip -r $(popd)/surf.zip ./surf/{??.pial,??.sphere.reg,??.thickness,??.volume,??.area,??.sulc,??.curv,??.avg_curv}
popd

echo "uploading recon output"

python3 upload.py $2 $XNAT_USER $XNAT_PASS $3

