===============================
My Brain and Me
===============================

Cookiecutter MBAM

Quickstart ('docker' configuration)
----------

To spin up a non-dockerized version of the app for development, you can skip steps 1 and 6 below.

1. If you haven't already, the first step is to [install Docker](https://docs.docker.com/install/). If you're using Linux,you may need to also install docker-compose using [this link](https://docs.docker.com/compose/install/). Be sure to use the link since default apt repositories may not have up to date version of docker-compose that is required to read yml version 3 files.

2. Clone this repository:
   `git clone https://github.com/spiropan/mbam`
   (or clone via ssh)

   To clone a specific branch:

   `git clone --single-branch -b development https://github.com/spiropan/mbam`

3. Install a local version of XNAT using [these instructions](https://wiki.xnat.org/display/XNAT17/Running+XNAT+in+a+Vagrant+Virtual+Machine). Use the one-line XNAT setup.  You will know it has worked when you can navigate to 10.1.1.17 in your browser and get an XNAT login page. The login and password are both 'admin', which of course you can change in your configuration if you wish. The above link also explains what you need to know to interact with and control your local XNAT. You will also need to install the XNAT Container services plugin. You can find instructions [here](https://github.com/MIND-NYSPI/xnat-cs-tutorial/blob/master/tutorial_part1.md#installing-the-container-service-plugin).

4. You'll need an XNAT project and you'll need to replace the DicomToNifti.xml pipeline with the custom pipeline in the repository. For the project, log in to your XNAT instance and go to **New -> Project**. Fill out the values for Project Title , Running Title, and Project ID and set to 'MBAM_TEST'.

(THE FOLLOWING COMMAND IS DEPRECATED AND WILL BE REPLACED WITH DCM2NIIX CONTAINER SERVICE)
  For the pipeline file (required for .zip uploading), copy the ./pipelines/DicomToNifti.xml in the MBAM repository to the /data/xnat/pipeline/catalog/mricron/ folder in the xnat VM that was installed in step 3. You should be able to use the "vagrant ssh" command and the share directories that were set up in step 3 above to transfer the file. If you get stuck with this let us know and we'll improve the instructions. You'll then need to add the pipeline to the site (Administer -> Pipelines -> Add Pipeline to Repository), and then also to the project (On the project page, press the Pipelines tab and then click Add More Pipelines).

5. You will need a configuration file called setup.cfg in the ./cookiecutter_mbam folder to bootstrap the app for development. See [bottom of this readme](cookiecutter_mbam/README.rst) for a description of the file.

6. To spin up a dockerized version of the app (that includes docker containers for Flask App, NGINX, MySQL, JATOS, REDIS and CELERY, but not XNAT), see below:

   `docker-compose up -d`

   Note that on your local environment, this command will load from the docker-compose.yml file, and then add the settings in the docker-compose.override.yml file. On the staging server (dev.mybrainandme.org), the startup command would be

   `docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml`

   while on the production server, the command would be

   `docker-compose -f docker-compose.yml -f docker-compose.prod.yml`

   The docker-compose.override.yml and the docker-compose.dev.yml are (for now) identical, but they both exist in order to 1) shorten the startup command on local environments and 2) allow for any future additional settings to be set and tested on the staging server.

7. During development, it is more convenient to work on the web app in DEBUG mode outside of docker, rather than work on the dockerized version of the app. For this, follow [these instructions](cookiecutter_mbam/README.rst) in the cookiecutter_mbam subfolder.  

   The above step will set up a sqlite db file for development. You can also set up another DBMS such as a dockerized mysql service. To do this type the below commands:

   `docker-compose down`

   then

   `docker-compose up -d mysql`

   You can also include a dockerized JATOS by running the above command and replacing 'mysql' with 'jatos', or you can install a local JATOS server using the [non-dockerized method](https://www.jatos.org/JATOS-on-a-server.html).
