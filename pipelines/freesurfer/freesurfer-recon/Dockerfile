FROM brainlife/freesurfer:7.1.0

RUN yum install -y python3-pip zip && pip3 install requests

RUN mkdir /input && mkdir /output && mkdir /output/uploads && mkdir /output/uploads/stats && mkdir /output/uploads/surf && mkdir /output/currsub

ENV SUBJECTS_DIR=/output

COPY resources/license.txt /opt/freesurfer/

COPY resources /usr/local/src

COPY currsub /output/currsub/

WORKDIR /usr/local/src

RUN chmod +x main.sh


