#!/bin/bash

# Convert any numbered and labeled value from FreeSurfer aseg to an obj file.

# usage
if [[ "$1" == "" ]]; then
    echo "Usage:"
    echo ""
    echo "    $ fs_extract_subregion.sh Subject001 99"
    echo ""
    echo "This will use FreeSurfer's SUBJECT_DIR variable and the subject, 'Subject001'"
    echo "to extract subcortical structure labelled #99 from aseg.mgz. It will create"
    echo "an object file for it and save it to a '3d' subdirectory for the subject."
    exit 0
fi
# Make sure the context is workable.
if [[ ! -e "$SUBJECTS_DIR/$1/mri/aseg.mgz" ]]; then
    echo "I cannot find the aseg.mgz file I need. Please check environment and arguments."
    echo "    SUBJECTS_DIR is \"$SUBJECTS_DIR\""
    echo "    You specified subject \"$1\""
    exit 0
fi

# Start the process
cd $SUBJECTS_DIR/$1/

mkdir -p ./tmp
mkdir -p ./3d

# Find a string label for the id specified
LBL="Unknown"
re="^[[:space:]]*([[:digit:]]+)[[:space:]]+(${2})[[:space:]]+[[:digit:]]+[[:space:]]+[[:digit:]]+\.[[:digit:]]+[[:space:]]+([-_[:alnum:]]+)[[:space:]]+.*$"
while IFS= read -r line; do
  [[ $line =~ $re ]] && LBL=( "${BASH_REMATCH[3]}" )
done <$SUBJECTS_DIR/$1/stats/aseg.stats

if [ ! -f ./tmp/aseg.nii ]; then
    mri_convert ./mri/aseg.mgz ./tmp/aseg.nii
fi
mri_binarize --i ./tmp/aseg.nii --match $2 --o ./tmp/$2-00.nii
mri_pretess ./tmp/$2-00.nii 1 ./mri/norm.mgz ./tmp/$2-01.nii
fslmaths ./tmp/$2-01.nii -bin ./tmp/$2-02.nii
mri_tessellate ./tmp/$2-02.nii 1 ./tmp/$2-final
mris_convert ./tmp/$2-final ./3d/$( printf '%03d' "$2" )-$LBL.stl

rm -rf ./tmp/${2}-*

cd -
