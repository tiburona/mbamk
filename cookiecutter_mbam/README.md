
# My Brain and Me 

My Brain and Me is a website that lets users upload their brain MRIs and get back an interactive visualization of their own brain.
  
## Setting Up an Environment for Local Development and Testing.  

### 1. Install dependencies

Install recent versions of Node and pipenv.  

Next navigate to the directory where you'd like to set up your environment and run the following commands to clone the repository and install dependencies: 
  
    git clone https://github.com/spiropan/mbam  
    cd mbam/cookiecutter_mbam  
    pipenv install --dev  
    npm install  
  
### 2. Set up the database

Install a recent version of MySQL. (As of this writing, the current version is 8.0).  If on MacOS, do this with: `brew install mysql`.

After installing MySQL, you must create the database user with the requisite permissions and create the database. Start MySQL:

    brew services start mysql

(If you do not have services installed, first run:

`brew tap homebrew/services`

Then from the mysql prompt:

    mysql> CREATE USER 'mbam'@'localhost' IDENTIFIED BY 'mbam123';
    mysql> GRANT ALL PRIVILEGES on brain_db.* TO 'mbam'@'localhost';
    mysql> QUIT

Back at your command line prompt:		

    mysql -u mbam -p

When prompted for the password, enter `mbam123`.

Create the database:

    mysql>  CREATE DATABASE brain_db;

Back on the command line, upgrade your new database so that it has the MBAM tables.  (You can do this from a different terminal window to avoid closing out of MySQL.  Just make sure to `cd` into mbam/cookiecutter_mbam.)

    flask db init  
    flask db migrate  
    flask db upgrade

Finally, check to make sure all your tables were created in MySQL:

    mysql> use brain_db
    mysql> show tables;

### 3. Start the webserver

If you are in the mbam/cookiecutter_mbam directory, these commands will start the server:

    pipenv shell
    npm start

Visit http://0.0.0.0:8000 to see the welcome screen.

### 4. Run Redis and Celery

MBAM depends on Redis and Celery to perform distributed tasks.  For local development, these services must be started seperately.

In a new terminal window, run Redis:

    redis-server

And in a third terminal window, run Celery: 

    celery -A cookiecutter_mbam.run_celery:celery worker --pool=gevent --concurrency=500 --loglevel info


That's it! Now you have a running local installation of MBAM that you can use for development.  (Steps 1 and 2 will not need to be repeated, but 3 and 4 must be performed every time you want to spin up the server.)


## Contributing

Thank you for contributing to MBAM!  To contribute, please pull the latest version of the `development` branch and make a branch off of it.  

### What else you need

MBAM uses XNAT, software that orchestrates neuroimaging workflows, to interface with Docker containers.  In order to run MBAM, you must either 

When you have finished your feature or bug fix, first checkout development, pull any changes from the remote, and merge those changes into your local branches.  Be sure to resolve any merge conflicts.  Once you have an unconflicted branch, commit your work and test your branch following the steps in the next section.  If your branch passes automated and manual tests, open a PR and request review.  You should have at least one reviewer who did not contribute to the development of your branch.    



## Testing MBAM

### 1. Run automated tests in the local development environment

From the mbam/cookiecutter_mbam directory run:

    flask test

### 2.  Run automated tests in the docker environment

MBAM must be dockerized to be deployed on Amazon servers.  To run MBAM's test in the docker environment, navigate to the root mbam directory and run:

    docker-compose build && docker-compose -f test.yml up

### 3. Test that migrations work.  

Whether or not you've made changes to any of the MBAM models, you should test that you are committing a series of migration files that are continuous with the migration files in the latest version of development, that run without error, and that bring a new database up-to-date with your current models.

In order to do this, log into MySQL again:

    mysql -u mbam -p

and enter the password `mbam123` at the command prompt.

Then

    mysql> drop database brain_db;
    mysql> create database brain_db;

Now, back at your command line in mbam/cookiecutter_mbam, run:

    flask db upgrade

Now back at the mysql prompt:

    mysql> use database brain_db;
    mysql> show tables;

And if you've made changes to the models and you want to make sure that this upgrade is current, you can inspect the tables individually with `show columns from <tablename>;`, for example:

    mysql> show columns from scan;

### 4. Manually test the website

As of this writing, an MBAM user should be able to upload up to 3 scans at a time.  Those files can be in one of three formats: a .zip file of DICOMS, an uncompressed NIFTI file (.nii) and a compressed NIFTI file (.nii.gz).  A users uploaded files should be saved both to an S3 bucket and to an XNAT instance hosted by Columbia.  

Upon upload, MBAM should automatically convert DICOM files to NIFTI, if applicable, and then kick off the Freesurfer reconstruction process, which runs in a Docker container also hosted on a Columbia server.  At the end of this process MBAM should transfer the output files from the Docker container to XNAT and S3.  The MBAM database should be updated with the S3 and XNAT locations of the original uploaded scan, the NIFTI files (but only if a conversion was performed), and the Freesurfer output.

Because Freesurfer reconstruction is a many-hour process in the best case, for testing purposes it is best to use a mock Freesurfer container that provides output as if Freesurfer ran.  
























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

If you add or delete columns in the database in a models.py file, then a database migration needs to be made. Whenever a database migration needs to be made. Run the following commands ::

    flask db migrate

This will generate a new migration script in cookiecutter_mbam/migrations/versions folder. Make sure to check this file and edit it manually if need be, because Alembic does not detect every change automatically. Then run ::

    flask db upgrade

To apply the migration and change the underlying database. If this is not successful, you may need to go back and edit the migration file. When successful (and the changes are applied to your local database), then be sure to commit the alembic migration file (in cookiecutter_mbam/migrations/versions folder) to git.

For a full migration command reference, run ``flask db --help``.

There are some catches. Flask migrate doesn't work 100% with SQLite, and contraints need to be named for upgrades and downgrades to work as expected (i.e. op.create_foreign_key('scan_user_id_fk', 'scan', 'user', ['user_id'], ['id']) instead of op.create_foreign_key(None, 'scan', 'user', ['user_id'], ['id']))

In addition, even if flask db upgrade works locally with mysql, it can still fail in production.
One way this can happen is when making changes to a field if it is used as a foreign key. The type and definition of foreign key field and reference must be equal. This means your foreign key disallows changing the type of your field.

The below example will trigger an error. Take home message, make sure to define fields properly before production, especially if they are being used as foreign keys.

Revision #1
op.add_column('scan', sa.Column('user_id', sa.Integer(), nullable=True))

Revision #2
op.alter_column('scan', 'user_id',
            existing_type=mysql.INTEGER(display_width=11),
            nullable=False)



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

    celery -A cookiecutter_mbam.run_celery:celery worker --pool=gevent --concurrency=500 --loglevel info

During development it might be helpful to see a graphic display of what the celery workers are up to. For this run the below command and open http://0.0.0.0:5555 in your web browser

    flower -A cookiecutter_mbam.run_celery:celery --port=5555


MYSQL
-----
For 'local' development, SQLite is OK. But SQLite has too many issues when using flask db migrate (see https://github.com/miguelgrinberg/Flask-Migrate/issues/97). Therefore if you're making changes to the models.py it's better to test migrations using a local installation of MySQL.

To do this:

  1) If on Mac OS X, install MySQL following https://gist.github.com/operatino/392614486ce4421063b9dece4dfe6c21
    Briefly, install Homebrew, then run brew install mysql@5.7
  2) Install MySQL Workbench (https://dev.mysql.com/downloads/workbench/)
  3) Add below to your .bash_profile (from https://stackoverflow.com/questions/30990488/how-do-i-install-command-line-mysql-client-on-mac)

     export PATH=$PATH:/Applications/MySQLWorkbench.app/Contents/MacOS

  3) Start mysql to connect to the service
    % brew services start mysql@5.7
    (note you may need to install services through brew first with "brew tap homebrew/services")
  4) In terminal type 'mysql -u root' to connect to mysql, then run:
    mysql> GRANT ALL PRIVILEGES ON *.* TO 'mbam'@'localhost' IDENTIFIED BY 'mbam123';
    mysql> create database brain_db;

Then you should be able to connect to mysql with "mysql -u mbam -p mbam123"

<!--stackedit_data:
eyJoaXN0b3J5IjpbOTk2NzYwMzUzLC05MzYyNTI4MTEsLTE4NT
M0MjU5NzIsMTM1MDUyMTIyMCwyMDg3MDMxMDI2XX0=
-->