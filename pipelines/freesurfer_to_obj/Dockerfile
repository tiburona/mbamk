FROM ubuntu:latest


# RUN apk update && apk upgrade && apk add bash openblas python3
RUN apt-get update && apt-get upgrade -y && apt-get install -y bash libopenblas-base libgomp1 python3 python3-pip zip
RUN pip3 install requests
RUN pip3 install pyopenssl ndg-httpsclient pyasn1

COPY resources /usr/local/src
COPY ./resources/*.conf ./resources/license.txt /usr/local/
COPY ./resources/bin /usr/local/bin

WORKDIR /usr/local/src

RUN mkdir /subjects
RUN mkdir /subjects/currsub
RUN mkdir /subjects/currsub/stats /subjects/currsub/surf /subjects/currsub/mri /subjects/currsub/tmp /subjects/currsub/3d

ENV SUBJECTS_DIR /subjects
ENV FREESURFER_HOME /usr/local
ENV FSLOUTPUTTYPE NIFTI

RUN chmod +x main.sh




