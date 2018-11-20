There are five configuration files that define environment variables included in the repo. These are in addition to settings that are set in the cookiecutter_mbam/settings.py file. Two files in the top level directory define environment variables for dockerized versions of the app.

   The first is named `.env` and defines the nginx configuration to be based to docker nginx.

   `NGINX_CONFIG_FILE=local.conf`

   The second file is named `jatos_config.env` and defines parameters for JATOS to connect to the
   dockerized MySQL db.

   ```
   JATOS_DB_URL=jdbc:mysql://mysql/brain_db?characterEncoding=UTF-8&useSSL=false
   JATOS_DB_USERNAME=mbam
   JATOS_DB_PASSWORD=mbam123
   JATOS_DB_DRIVER=com.mysql.jdbc.Driver
   JATOS_JPA=mysqlPersistenceUnit
   ```

   In cookiecutter_mbam subfolder, there are three files. One is the .env file which defines env variables for the flask app when spun up outside of docker:

   ```
   FLASK_APP=autoapp.py
   FLASK_ENV=development
   DATABASE_URL=sqlite:////tmp/dev.db
   SECRET_KEY='not-so-secret'
   FLASK_RUN_PORT=8000
   FLASK_RUN_HOST=0.0.0.0
   ```

   The other file is the .docker_env which includes configuration for the dockerized version of
   the flask app. This file is copied over the above .env in the app's Dockerfile:

   ```
   FLASK_APP=autoapp.py
   FLASK_ENV=production
   DATABASE_URL=mysql+pymysql://mbam:mbam123@mysql/brain_db
   SECRET_KEY='not-so-secret'
   FLASK_RUN_PORT=8000
   FLASK_RUN_HOST=0.0.0.0
   ```

   The third file is cookiecutter_mbam/setup.cfg which defines the parameters for the XNAT connection.

   ```
   [flake8]
   ignore = D401
   max-line-length=120

   [XNAT]
   user = admin
   password = admin
   server = http://10.1.1.17
   project = MBAM_TEST

   [uploads]
   uploaded_scans_dest = /static/files
   uploaded_scans_url = http://0.0.0.0:8000/static/files/
   ```

   This file replaces the older version originally called `app_config.env`.  It not used now but is shown below for reference:

   ```
   XNAT_USER=admin # or <your-xnat-user> if you changed it
   XNAT_PSWD=admin # or <your-password> if you changed it
   XNAT_PROJECT=MBAM_TEST # or <your-project-name> if you named it something else
   XNAT_URL=http://10.1.1.17 # or https://mind-xnat.nyspi.org if you are using a sandbox project on the MIND site.
   ````
