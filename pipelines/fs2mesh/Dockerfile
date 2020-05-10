FROM ubuntu:18.04

ENV SUBJECTS_DIR=/subjects
ENV FREESURFER_HOME=/opt/fs2mesh
ENV FSLOUTPUTTYPE=NIFTI
ENV PATH=${PATH}:/opt/blender:/opt/fs2mesh

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install bash libopenblas-base python3 wget xz-utils libgomp1 -y \
    && apt-get install libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 -y \
    && apt-get install python3 python3-pip zip -y

RUN pip3 install requests

RUN for DIR in stats surf mri touch scripts label mesh tmp; do mkdir -p ${SUBJECTS_DIR}/currsub/${DIR}; done

RUN mkdir -p /opt/fs2mesh/ && cd /opt/ \
    && wget -q https://download.blender.org/release/Blender2.82/blender-2.82a-linux64.tar.xz \
    && tar -xf blender-2.82a-linux64.tar.xz \
    && rm blender-2.82a-linux64.tar.xz \
    && ln -s /opt/blender-2.82a-linux64 /opt/blender

COPY ./resources/*.py ./resources/*.sh /usr/local/src/
COPY ./resources/*.conf ./resources/license.txt /opt/fs2mesh/
COPY ./resources/bin /opt/fs2mesh/

WORKDIR /usr/local/src

RUN chmod +x main.sh




