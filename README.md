1. If you haven't already, the first step is to [install Docker](https://docs.docker.com/install/). If you're using Linux,
you may need to also install [docker-compose](https://docs.docker.com/compose/install/).

2. Clone this repository:  
`git clone https://github.com/spiropan/mbam`  
(or clone via ssh)

3. Install a local version of XNAT.  Instructions are [here](https://wiki.xnat.org/display/XNAT17/Running+XNAT+in+a+Vagrant+Virtual+Machine).  Use the one-line XNAT setup.  You will know it has worked when you can navigate to 10.1.1.17 in your browser and get an XNAT login page.  The login and password are both 'xnat', which of course you can change in your configuration if you wish.

4. You'll need an XNAT project.  Log in to your XNAT instance and go to **New -> Project**.  Fill out the values for Project Title, Running Title, and Project ID

5. There are three configuration files that should be placed in the top-level directory.  The first should be named `.env`.  It needs only the following line:  

   `NGINX_CONFIG_FILE=local.conf`

   The second is called `app_config.env`.  It should begin like this:

   ```
   SECRET_KEY=you-will-never-guess
   DB_ROOT_PASSWORD=test
   DB_HOST=mysql
   DB_USERNAME=mbam
   DB_PASSWORD=mbam123
   ```

   `DB_USERNAME` and `DB_HOST` should be kept the same; they are also set in the docker-compose file that configures the MySQL container.

   `app_config.env` then continues:

   ```
   XNAT_USER=admin # or <your-xnat-user> if you changed it
   XNAT_PSWD=admin # or <your-password> if you changed it
   XNAT_URL=10.1.1.7

   RUN_FROM=local
   ````
   The below are settings for running the pilot flirt and labeling pipeline (i.e. clicking the "Labeled MRI" in the main volume view. To run on your local XNAT you can install the Xsync plugin from [here](https://download.xnat.org/), sync MBAM_FILES project from the MIND-XNAT server, and note its XNAT session id. Documentation for how to setup and use the Xsync plugin [here](https://wiki.xnat.org/pages/viewpage.action?pageId=51642418).

   Optional: You will also need to install the container plugin, add a new image (mindnyspi/flirt-applyxfm) and copy the pipelines/flirt-reg-applyxfm/command.json into a new command under this image (see [part 1](https://github.com/MIND-NYSPI/xnat-cs-tutorial/blob/master/tutorial_part1.md) of the XNAT-CS-TUTORIAL). We will update/optimize this process in the near future. Use the below values if your XNAT_URL is https://mind-xnat.nyspi.org, otherwise adjust them for as needed for your local environment.

   ```
   XNAT_RESOURCES_ID=MIND_E08399
   FLIRT_COMMAND_ID=20
   ```

   Finally create a file named `jatos_config.env`.

   ```
   JATOS_DB_URL=jdbc:mysql://mysql/brain_db?characterEncoding=UTF-8&useSSL=false
   JATOS_DB_USERNAME=mbam
   JATOS_DB_PASSWORD=mbam123
   JATOS_DB_DRIVER=com.mysql.jdbc.Driver
   JATOS_JPA=mysqlPersistenceUnit
   ```

   Your `JATOS_DB_USERNAME` and `JATOS_DB_PASSWORD` should match their analogues in `app_config.env`: `DB_USERNAME` and `DB_PASSWORD`.

6. Once those configuration files are in place, run

   `docker-compose up -d`

   Note that on your local environment, this command will load from the docker-compose.yml file, and then add the settings in the docker-compose.override.yml file. On the staging server (dev.mybrainandme.org), the startup command would be

   `docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml`

   while on the production server, the command would be

   `docker-compose -f docker-compose.yml -f docker-compose.prod.yml`

   The docker-compose.override.yml and the docker-compose.dev.yml are (for now) identical, but they both exist in order to 1) shorten the startup command on local environments and 2) allow for any future additional settings to be set and tested on the staging server.
