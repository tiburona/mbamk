FROM freesurfer/freesurfer:6.0

COPY resources /usr/local/src

WORKDIR /usr/local/src

RUN mkdir /input && mkdir /output && mkdir /output/uploads && mkdir /output/uploads/stats && mkdir /output/uploads/surf

ENV SUBJECTS_DIR=/output

COPY resources/license.txt /opt/freesurfer/