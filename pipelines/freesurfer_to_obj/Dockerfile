FROM ubuntu:latest

RUN mkdir /subs
RUN mkdir /subs/currsub

ENV SUBJECTS_DIR /subs
ENV FREESURFER_HOME /usr/local
ENV FSLOUTPUTTYPE NIFTI



# RUN apk update && apk upgrade && apk add bash openblas python3
RUN apt-get update && apt-get upgrade -y && apt-get install -y bash libopenblas-base libgomp1 python3 python3-pip zip
RUN pip3 install requests

COPY resources /usr/local/src
COPY ./resources/*.conf ./license.txt /usr/local/
COPY ./resources/bin /usr/local/bin

WORKDIR /usr/local/src

RUN chmod +x main.sh




