#!/bin/bash

LOG=${SUBJECTS_DIR}/${1}/tmp/conversions.log

mkdir -p ${SUBJECTS_DIR}/${1}/tmp
mkdir -p ${SUBJECTS_DIR}/${1}/3d

# Convert pial surfaces to obj files
pial_to_obj.py ${SUBJECTS_DIR}/${1}/surf/lh.pial ${SUBJECTS_DIR}/${1}/3d/003-Left-Cerebral-Cortex.obj | tee -a ${LOG}
pial_to_obj.py ${SUBJECTS_DIR}/${1}/surf/rh.pial ${SUBJECTS_DIR}/${1}/3d/042-Right-Cerebral-Cortex.obj | tee -a ${LOG}

# Convert subcortical regions to stl files
while read f; do
    if [ "${f:0:1}" != "#" ]; then
        ID=${f%% *}
        if [ "${ID}" != "" ]; then
            echo "" >> ${LOG}
            echo "Running with arguments (\"${1}\", \"${ID}\") from \"${f}\"" | tee -a ${LOG}
            fs_extract_subregion.sh ${1} ${ID} >> ${LOG}
        else
            echo "Ignoring call with arguments (\"${1}\", \"${ID}\") from \"${f}\"" | tee -a ${LOG}
        fi
    fi
done </usr/local/freesurfer_to_obj.regions.conf

echo "Done"
