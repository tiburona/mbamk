
# My Brain and Me

My Brain and Me is a website that lets users upload their brain MRIs and get back an interactive visualization of their own brain.

## Setting Up an Environment for Local Development and Testing.

### 1. Install dependencies

Install recent versions of Node and pipenv.

Next navigate to the directory where you'd like to set up your environment and run the following commands to clone the repository and install dependencies:

    git clone https://github.com/spiropan/mbam
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

### 3. Install Redis

 See here: https://redis.io/topics/quickstart

### 4. Determine your level of permissions

MBAM has two kinds of local development environment, one named named 'trusted' and one named 'local'.  If you're reading this before we've open sourced the project, it's very likely you're a trusted developer.  Trusted developers can access a central set of credentials for MBAM.  Assuming you have an internet connection, there is only one set of credentials you need on your machine, the key ID/secret key pair that accesses the AWS parameter store.  Open `config/credentials/sample.secrets.yml` and enter the values you've been provided in for  `PARAMETER_STORE_KEY_ID` and `PARAMETER_STORE_SECRET_KEY`.  Change the name of the file to `secrets.yml`.  This file is in the .gitignore; of course it must never be committed to the repository.

### 5. Start the webserver

If you are in the mbam/cookiecutter_mbam directory, these commands will start the server if you're a trusted developer:

    pipenv shell
    npm start

`npm start` also starts a Redis server and a Celery worker.  You will see output from Redis, Celery, and Webpack in the same terminal window.

Visit http://0.0.0.0:8000 to see the welcome screen.

If you're not a trusted developer, you'll see a suggestion for another command you can run consistently to suppress the warning message: `npm run start-local`.


## Understanding the services used by MBAM

### 1. XNAT

MBAM uses XNAT, software that orchestrates neuroimaging workflows, to interface with Docker containers that process brain images.  In order to run MBAM, you must either set up your own XNAT installation or use one of the Columbia team's XNAT instances.  We have two: MIND XNAT and Backup XNAT.  If you are a trusted developer and you start the application using `npm start` by default you will be using MIND XNAT.  For more information on configuring MBAM's use of XNAT see [Advanced Configuration Options](#configuration).

### 2. Celery, Redis, and Flower

Celery runs MBAM's asynchronous operations.  All communications with XNAT are asynchronous processes.  Redis is the message broker and results backend for Celery. In the local development environment, the `start.py` script runs both a Redis server instance and a Celery worker with the commands

    redis-server

and

    celery -A cookiecutter_mbam.run_celery:celery worker --pool=gevent --concurrency=500 --loglevel info

respectively.

During development you may be interested in using Flower to monitor your Celery process.

Run

    flower -A cookiecutter_mbam.run_celery:celery --port=5555

and visit http://0.0.0.0:5555.

## Contributing

Thank you for contributing to MBAM!  To contribute, please pull the latest version of the `development` branch and make a branch off of it.

### What else you need

You must have a Docker installation, either on your own computer, a remote host, or both.

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





<a name="configuration"></a>
## Advanced Configuration Options

### 1. Choosing an XNAT instance

MBAM uses XNAT, software that orchestrates neuroimaging workflows, to interface with Docker containers.  In order to run MBAM, you must either set up your own XNAT installation or use one of the Columbia team's XNAT instances.  We have two: MIND XNAT and Backup XNAT.  If you are a trusted developer and you start the application using `npm start` by default you will be using MIND XNAT.  If you'd like to change this you have a couple of options.

 1. Add a `.env `file to the top level directory that has five variables: `XNAT_HOST`, `XNAT_USER,`  `XNAT_PASSWORD`, `DICOM_TO_NIFTI_COMMAND`, and `FREESURFER_RECON_COMMAND`.  If you don't know the latter two values for your XNAT instance, you can figure them out In this project we conceive of `.env`files as being designed for idiosyncratic or ephemeral adjustments a developer might make to their local environment.  For this reason`.env`is included in the `.gitignore`; please don't commit it to the repo.

 2.  Invoke the project's `start.py` script directly.  This is the script that `npm start` calls to run the project.  It's found in the `tools` directory.  A list of arguments to `start.py` can be found by running `tools/start.py -h`.  One fo the arguments is `--xnat`.  As of this writing, the choices are `mind` and `backup`.  If you start the app like this
`python tools/start.py -frc --config_dir config --xnat backup`
you will configure it to use the backup XNAT instance.

Note that any variables configured in a `.env` file have higher precedence than configuration from environment variables.