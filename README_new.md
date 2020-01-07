
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

Now you have a running local installation of MBAM that you can use for development.  (Steps 1 and 2 will not need to be repeated, but 3 and 4 must be performed every time you want to spin up the server.)

### 5. Choose an XNAT instance

MBAM uses XNAT, software that orchestrates neuroimaging workflows, to interface with Docker containers.  In order to run MBAM, you must either set up your own XNAT installation or use one of the Columbia team's XNAT instances.  We have two: MIND XNAT

## Contributing

Thank you for contributing to MBAM!  To contribute, please pull the latest version of the `development` branch and make a branch off of it.

### What else you need



You must have a Docker installation, either on your own computer, a remote host, or both.  Docker has two

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
