===============================
My Brain and Me
===============================

Cookiecutter MBAM

Quickstart ('docker' configuration)
----------

To spin up a non-dockerized version of the app for development, you can skip steps 1 and 6 below or go directly to [these instructions](cookiecutter_mbam/README.md). For instructions on committing to 'master' see bottom of this file.

1. If you haven't already, the first step is to [install Docker](https://docs.docker.com/install/). If you're using Linux,you may need to also install docker-compose using [this link](https://docs.docker.com/compose/install/). Be sure to use the link since default apt repositories may not have up to date version of docker-compose that is required to read yml version 3 files.

2. Clone this repository:
   `git clone https://github.com/spiropan/mbam`
   (or clone via ssh)

   To clone a specific branch:

   `git clone --single-branch -b development https://github.com/spiropan/mbam`

3. In order to upload brain scans you need to set up access to an XNAT server, either a locally installed one or a remote server.

LOCAL XNAT (OPTIONAL): Install a local version of XNAT using [these instructions](https://wiki.xnat.org/display/XNAT17/Running+XNAT+in+a+Vagrant+Virtual+Machine). Use the one-line XNAT setup.  You will know it has worked when you can navigate to 10.1.1.17 in your browser and get an XNAT login page. The login and password are both 'admin', which of course you can change in your configuration if you wish. The above link also explains what you need to know to interact with and control your local XNAT. You will also need to install the XNAT Container services plugin. You can find instructions [here](https://github.com/MIND-NYSPI/xnat-cs-tutorial/blob/master/tutorial_part1.md#installing-the-container-service-plugin).

REMOTE XNAT: you can use the MIND XNAT server which will work for development as long as you have network access (and a username, password and project folder on the XNAT server). Ask Spiro to create an account if you don't already have one.

4. Create a XNAT project folder for development. Log in to your XNAT and go to **New -> Project**. Fill out the values for Project Title , Running Title, and Project ID and set to i.e. 'MBAM_SOMENAME'.

5. If you are using the remote XNAT option you will need to add below environment variables in your shell using i.e. .bash_profile or .bashrc. This is also required for the dockerized version of the app. For values in brackets talk to Spiro.

export XNAT_HOST={XNAT_HOST}
export XNAT_USER={XNAT_USER}
export XNAT_PASSWORD={XNAT_PASSWORD}
export XNAT_PROJECT={XNAT_PROJECT}
export DOCKER_HOST={DOCKER_HOST}
export DICOM_TO_NIFTI_TRANSFER_COMMAND_ID={DICOM_TO_NIFTI_TRANSFER_COMMAND_ID}

6. To spin up a dockerized version of the app (that includes docker containers for Flask App, NGINX, MySQL, JATOS, REDIS and CELERY, but not XNAT), see below:

   `docker-compose up -d`

   Note that on your local environment, this command will load from the docker-compose.yml file, and then add the settings in the docker-compose.override.yml file. On the staging server (dev.mybrainandme.org), the startup command would be

   `docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml`

   while on the production server, the command would be

   `docker-compose -f docker-compose.yml -f docker-compose.prod.yml`

   The docker-compose.override.yml and the docker-compose.dev.yml are (for now) identical, but they both exist in order to 1) shorten the startup command on local environments and 2) allow for any future additional settings to be set and tested on the staging server.

7. During development, it is more convenient to work on the web app in DEBUG mode outside of docker, rather than work on the dockerized version of the app. For this, follow [these instructions](cookiecutter_mbam/README.md) in the cookiecutter_mbam subfolder.  

   The above step will set up a sqlite db file for development. You can also set up another DBMS such as a dockerized mysql service. To do this type the below commands:

   `docker-compose down`

   then

   `docker-compose up -d mysql`

   You can also include a dockerized JATOS by running the above command and replacing 'mysql' with 'jatos', or you can install a local JATOS server using the [non-dockerized method](https://www.jatos.org/JATOS-on-a-server.html).

==================  Merging to master or development branch =================================

Make sure to follow below steps before a pull request to master or development branch.

1. Make sure your branch passes unit tests. If using a 'local' environment run the below command in
mbam/cookiecutter_mbam folder

  `flask test`

For anything other than UI development, you should also make sure the unit tests pass in the 'docker' environment. For this run the below command in the root folder /mbam:

  `docker-compose -f test.yml up`

2. Manually test and verify that NIFTI and DICOM file upload work on the remote MIND XNAT server, both in the 'local' and 'docker' environments.
