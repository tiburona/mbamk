# freesurfer_to_obj

Convert FreeSurfer segmentations to WaveForm *.obj and *.stl files

Pull the repo.

    git clone git@github.com:mfschmidt/freesurfer_to_obj.git
    cd freesurfer_to_obj.git

Copy your own FreeSurfer license file (free from https://surfer.nmr.mgh.harvard.edu/registration.html). Obviously, use whatever path contains your license, or just download it here.

    cp /opt/freesurfer/license.txt ./

Build a docker image.

    docker build . -t freesurfer_to_obj

Run it.

    docker run -v $SUBJECTS_DIR:/subjects freesurfer_to_obj subjid

This should extract each hemisphere and many subcortical regions and save them as object files in $SUBJECTS_DIR/subjid/3d/

You can explore the container and manually run things with the following:

    docker run -it -v $SUBJECTS_DIR:/subjects --entrypoint /bin/bash freesurfer_to_obj
