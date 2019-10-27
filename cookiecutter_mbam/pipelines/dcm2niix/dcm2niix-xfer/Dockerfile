FROM xnat/dcm2niix

COPY resources /usr/local/src

WORKDIR /usr/local/src

RUN mkdir /input && mkdir /output

RUN apt-get update

RUN apt-get install -y python3-pip && pip3 install requests

RUN chmod +x main.sh

