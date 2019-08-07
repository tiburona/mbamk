===============================
My Brain and Me
===============================

Cookiecutter MBAM

Quickstart ('local' configuration)
----------

Be sure to first install recent versions of Node/NPM and pipenv (i.e. pip install pipenv).
Then run the following commands to bootstrap your environment

    git clone https://github.com/spiropan/mbam # To clone the master branch
    cd mbam/cookiecutter_mbam
    pipenv install --dev
    npm install
    pipenv shell
    npm start  # run the webpack dev server and flask server using concurrently

If you orient your browser to http://0.0.0.0:8000 you will see a pretty welcome screen.

    After running the above commands the first time, to spin up the app on your machine
    again type the below commands ::

    cd mbam/cookiecutter_mbam
    pipenv shell
    npm start

The above steps will create and write the DB to a /tmp/dev.db sqlite file. This should
work well enough for development. Follow the steps below if you want to work with a different
DBMS. Remember to change $DATABASE_URL in the .env included with the repo.

Once you have installed your DBMS, run the following to create your app's
database tables and perform the initial migration.

    flask db init
    flask db migrate
    flask db upgrade
    npm start


Deployment
----------

The below is part of the autogenerated docs, but is left here for reference.
These steps are implemented as part of running the dockerized version of the flask app.
See the main README at the root directory of the repo.

To deploy:

    export FLASK_ENV=production
    export FLASK_DEBUG=0
    export DATABASE_URL="<YOUR DATABASE URL>"
    npm run build   # build assets with webpack
    flask run       # start the flask server

In your production environment, make sure the ``FLASK_DEBUG`` environment
variable is unset or is set to ``0``.


Shell
-----

To open the interactive shell, run ::

    flask shell

By default, you will have access to the flask ``app``.


Running Tests
-------------

To run all tests, run ::

    flask test

Migrations
----------

Whenever a database migration needs to be made. Run the following commands ::

    flask db migrate

This will generate a new migration script. Then run ::

    flask db upgrade

To apply the migration.

For a full migration command reference, run ``flask db --help``.


Asset Management
----------------

Files placed inside the ``assets`` directory and its subdirectories
(excluding ``js`` and ``css``) will be copied by webpack's
``file-loader`` into the ``static/build`` directory, with hashes of
their contents appended to their names.  For instance, if you have the
file ``assets/img/favicon.ico``, this will get copied into something
like
``static/build/img/favicon.fec40b1d14528bf9179da3b6b78079ad.ico``.
You can then put this line into your header::

    <link rel="shortcut icon" href="{{asset_url_for('img/favicon.ico') }}">

to refer to it inside your HTML page.  If all of your static files are
managed this way, then their filenames will change whenever their
contents do, and you can ask Flask to tell web browsers that they
should cache all your assets forever by including the following line
in your ``settings.py``::

    SEND_FILE_MAX_AGE_DEFAULT = 31556926  # one year

Celery
------

In order to have the site's asynchronous functions operate with Celery you must `install Redis <https://redis.io/topics/quickstart>`_
and invoke it with the command ``redis-server``.

You also must invoke a Celery worker in a different process.  In the current development environment, this the command to do so:

    celery -A cookiecutter_mbam.run_celery:celery worker --loglevel info``

Setup.cfg File
--------------

To configure the app for XNAT include the below parameters in the setup.cfg file
and store it in the 'cookiecutter_mbam' folder. VAR are parameters that
need to set by each developer.

  [flake8]
  ignore = D401
  max-line-length=120

  [XNAT]
  user = admin
  password = admin
  server = http://10.1.1.17
  project = MBAM_TEST
  local_docker = True
  docker_host = unix:///var/run/docker.sock
  dicom_to_nifti_command_id = VAR
  dicom_to_nifti_wrapper_id = dcm2niix-scan
  dicom_to_nifti_transfer_command_id = VAR
  dicom_to_nifti_transfer_wrapper_id = dcm2niix-xfer

  [AWS]
  access_key_id = VAR
  secret_access_key = VAR
  bucket_name = VAR

  [files]
  file_depot = static/files/
  file_depot_url = http://0.0.0.0:8081/static/files/  