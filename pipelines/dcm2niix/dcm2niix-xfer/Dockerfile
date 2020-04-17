FROM xnat/dcm2niix

RUN apt-get update

RUN apt-get install -y python3-pip && pip3 install requests

COPY resources /usr/local/src

WORKDIR /usr/local/src

RUN mkdir /input && mkdir /output

RUN chmod +x main.sh

