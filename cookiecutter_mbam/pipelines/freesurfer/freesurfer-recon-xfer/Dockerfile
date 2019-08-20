FROM freesurfer/freesurfer:6.0

COPY resources /usr/local/src

WORKDIR /usr/local/src

RUN mkdir /input && mkdir /output && mkdir /output/uploads && mkdir /output/uploads/stats && mkdir /output/uploads/surf

ENV SUBJECTS_DIR=/output

RUN apt-get update

RUN apt-get install -y python3-pip && pip3 install requests

RUN chmod +x main.sh

COPY resources/license.txt /opt/freesurfer/