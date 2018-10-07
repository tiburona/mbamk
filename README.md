1. If you haven't already, the first step is to [install Docker](https://docs.docker.com/install/). If you're using Linux,
   you may need to also install docker-compose using [this link](https://docs.docker.com/compose/install/). Be sure to use the link since
   default apt repositories may not have up to date version of docker-compose that is required to read yml version 3 files.

2. Clone this repository:
   `git clone https://github.com/spiropan/mbam`
   (or clone via ssh)

3. Install a local version of XNAT using [these instructions](https://wiki.xnat.org/display/XNAT17/Running+XNAT+in+a+Vagrant+Virtual+Machine).
   Use the one-line XNAT setup.  You will know it has worked when you can navigate to 10.1.1.17 in your browser and get an XNAT login page.
   The login and password are both 'admin', which of course you can change in your configuration if you wish.
   The above link also explains what you need to know to interact with and control your local XNAT. You will also need to install
   the XNAT Container services plugin. You can find instructions [here](https://github.com/MIND-NYSPI/xnat-cs-tutorial/blob/master/tutorial_part1.md#installing-the-container-service-plugin).

4. You'll need an XNAT project and you'll need to replace the DicomToNifti.xml pipeline with the custom pipeline in the repository.
   For the project, log in to your XNAT instance and go to **New -> Project**.  Fill out the values for Project Title , Running Title,
   and Project ID and set to 'MBAM_TEST'. For the pipeline file (required for .zip uploading), copy the ./pipelines/DicomToNifti.xml
   in the MBAM repository to the /data/xnat/pipeline/catalog/mricron/ folder in the xnat VM that was installed in step 3. You should be
   able to use the "vagrant ssh" command and the share directories that were set up in step 3 above to transfer the file. If you get
   stuck with this let us know and we'll improve the instructions. You'll then need to add the pipeline to the site
   (Administer -> Pipelines -> Add Pipeline to Repository), and then also to the project (On the project page, press the Pipelines
   tab and then click Add More Pipelines).

5. There are three configuration files that should be placed in the top-level directory.  The first should be named `.env`.  It needs
   only the following line:

   `NGINX_CONFIG_FILE=local.conf`

   The second is called `app_config.env`.  It should have the below lines (without the comments):

   ```
   XNAT_USER=admin # or <your-xnat-user> if you changed it
   XNAT_PSWD=admin # or <your-password> if you changed it
   XNAT_PROJECT=MBAM_TEST # or <your-project-name> if you named it something else
   XNAT_URL=http://10.1.1.17 # or https://mind-xnat.nyspi.org if you are using a sandbox project on the MIND site.
   ````

   Finally create a file named `jatos_config.env`.

   ```
   JATOS_DB_URL=jdbc:mysql://mysql/brain_db?characterEncoding=UTF-8&useSSL=false
   JATOS_DB_USERNAME=mbam
   JATOS_DB_PASSWORD=mbam123
   JATOS_DB_DRIVER=com.mysql.jdbc.Driver
   JATOS_JPA=mysqlPersistenceUnit
   ```

   Note that `JATOS_DB_USERNAME` and `JATOS_DB_PASSWORD` match their analogues that are set in the config.py for local development
   environments: `DB_USERNAME` and `DB_PASSWORD`.

6. Once those configuration files are in place, run

   `docker-compose up -d`

   Note that on your local environment, this command will load from the docker-compose.yml file, and then add the settings in the docker-compose.override.yml file. On the staging server (dev.mybrainandme.org), the startup command would be

   `docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml`

   while on the production server, the command would be

   `docker-compose -f docker-compose.yml -f docker-compose.prod.yml`

   The docker-compose.override.yml and the docker-compose.dev.yml are (for now) identical, but they both exist in order to 1) shorten the startup command on local environments and 2) allow for any future additional settings to be set and tested on the staging server.

7. During development, it is probably more convenient to work on the web app in DEBUG mode from your host environment, rather than work on the
   dockerized version of the app. For this, you will need to set up a virtual environment python2.7 (we're working to upgrade to 3 soon) install on your host
   machine. If you're unclear how to set this up see [this link](https://realpython.com/python-virtual-environments-a-primer/). After installing activating your
   virtual environment, navigate to ./mbam/web/ directory and install all required packages within the virtual environment with

   `pip install -r requirements.txt`

   You will then need to export the CONFIG_NAME to an environment variable in your terminal or add to your i.e .bashrc or .bash_profile. Be sure to start a new terminal
   or remove this from your .bash_profile if you want to start up the full dockerized version as outlined in step 6.

   `export CONFIG_NAME=debug`

   For this set up you only need the dockerized mysql service. Ignoring JATOS and NGINX for now, you can spin up just the mysql using the below command:

   `docker-compose down`

   then

   `docker-compose up -d mysql

   You should then be able to spin up the app by nagivating to ./mbam/web/flask_brain_db and running:

   `python manage.py runserver`

   You can also run the unittests with coverage using:

   `python manage.py cov`
