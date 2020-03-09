
# My Brain and Me

My Brain and Me is a website that lets users upload their brain MRIs and get back an interactive visualization of their 
own brain.

## Table of Contents 
  

[**Quickstart: Setting up an environment for local development and testing**](#setting-up-an-environment-for-local-development-and-testing)
1. [Install dependencies](#1-install-dependencies)  
2. [Choose your database](#2-choose-your-database)  
3. [Install Redis](#3-install-redis)  
4. [Determine your level of permissions](#4-determine-your-level-of-permissions)  
5. [Locally install the MBAM start package](#5-locally-install-the-mbam-start-package)  
6. [Start the webserver](#6-start-the-webserver)
    
[**Understanding the services used by MBAM**](#understanding-the-services-used-by-mbam)
1. [XNAT](#1-xnat)
2. [Celery, Redis, and Flower](#2-celery-redis-and-flower)
3. [AWS](#3-aws)
    - [Parameter Store](#parameter-store)
    - [S3](#s3)
    - [Cloudfront](#cloudfront)

[**Contributing**](#contributing)  
1. [Process](#1-process)
2. [What else you need](2-#what-else-you-need) 

[**More setup and configuration options**](#more-setup-and-configuration-options)
1. [Custom configuration with config overrride](#1-custom-configuration-with-config-overrride)  
2. [S3 configuration](#2-s3-configuration)
3. [XNAT configuration](#2-xnat-configuration)
    - [Configuration variables](#configuration-variables)
    - [Setting up the VVM - preliminaries](#setting-up-the-vvm---preliminaries) 
    - [Setting up the VVM or any other XNAT instance - Docker images and commands](#setting-up-the-vvm-or-any-other-xnat-instance---docker-images-and-commands)
        1. [Make XNAT communicate with Docker](#i-make-xnat-communicate-with-docker)
        2. [Build containers](#ii-build-containers)
4. [Database setup](#3-database-setup)
    - [MySQL Installation](#mysql-installation)
    - [Dockerized MySQL](#dockerized-mysql)

[**Testing**](#testing)
1. [Run automated tests in the local development environment](#1-run-automated-tests-in-the-local-development-environment)
2. [Run automated tests in the docker environment](#2--run-automated-tests-in-the-docker-environment)
3. [Test that migrations work](#3-test-that-migrations-work)
4. [Manually test the website](#4-manually-test-the-website)

[**Deployment**](#deployment)  
1. Nothing to see here yet

[**Resources**](#resources)
1. [XNAT](#1-xnat)


## Setting up an environment for local development and testing

If you just want to get up and running and poke around a bit, items 1-6 in this section will get you a local development
environment up and running.  

### 1. Install dependencies

Install recent versions of Node and pipenv.

Next navigate to the directory where you'd like to set up your environment and run the following commands to clone the repository and install dependencies:

    git clone https://github.com/spiropan/mbam
    pipenv install --dev
    npm install

### 2. Choose your database

To get development up and running quickly, SQLite, which is installed with MBAM, is sufficient.  If during development 
you plan to be making changes to the database tables, you will need MySQL, either locally installed or dockerized.
For instructions on locally installing MySQL and getting it up and running with MBAM, go to 
[Database Configuration](#1-database-installation).

### 3. Install Redis

 See here: https://redis.io/topics/quickstart

### 4. Determine your level of permissions

MBAM has two kinds of local development environment, one named named 'trusted' and one named 'local'.  If you're reading 
this before we've open sourced the project, it's very likely you're a trusted developer.  Trusted developers can access 
a central set of credentials for MBAM.  Assuming you have an internet connection, there is only one set of credentials 
you need on your machine, the key ID/secret key pair that accesses the AWS parameter store.  

Open `config/credentials/sample.secrets.yml` and enter the values you've been provided in for  `PARAMETER_STORE_KEY_ID` 
and `PARAMETER_STORE_SECRET_KEY`.  Change the name of the file to `secrets.yml`.  This file is in the .gitignore; of 
course it must never be committed to the repository.

### 5. Locally install the MBAM start package

As of this writing, the utility in the `tools/start` directory allows can run an MBAM development server (and its 
tests).  It can be executed as a regular Python program, but it is also packaged to allow it to be executed as a
standalone command line utility.  To install this package and also activate the pipenv shell, run

    . env.sh install

in the main directory.  After using the `install` argument once, every other time you can just run 

    . env.sh
    
(For more information about what the MBAM start package can do, `mbam -h`, `mbam run -h`, and `mbam test -h` will all be
informative.  `mbam deploy` is hopefully coming soon.)


### 6. Start the webserver

If you're a trusted developer, the last command you have to run is

    npm start

`npm start` also starts a Redis server and a Celery worker.  You will see output from Redis, Celery, and Webpack in the 
same terminal window.

Visit http://0.0.0.0:8000 to see the welcome screen.

    mbam run -fcr
    
will also work.  However, as of this writing color coding works better using `npm start`.

If you're not a trusted developer, you'll see a suggestion for another command you can run consistently to suppress the 
warning message: `npm run start-local`.

MBAM should now work out of the box if you're a trusted developer, although there's some further database setup for 
testing.  If you're not you still have some work to do to get everything you need configured to have a fully functional
MBAM.  Read on.


## Understanding the services used by MBAM

### 1. XNAT

MBAM uses XNAT, software that orchestrates neuroimaging workflows, to store user files and to interface with Docker 
containers that process brain images.  In order to run MBAM, you must either set up your own XNAT installation or use 
one of the Columbia team's XNAT instances.  We have two: MIND XNAT (accessible at https://mind-xnat.nyspi.org/) and 
Backup XNAT ( http://10.20.205.246:8080/).  You must be behind the NYSPI firewall to access Backup XNAT.  If you are a 
trusted developer and you start the application using `npm start` by default you will be using MIND XNAT.  

If you are not yet a trusted developer, you will need your own instance of XNAT.  The 
[one line XNAT installation](https://wiki.xnat.org/documentation/getting-started-with-xnat/running-xnat-in-a-vagrant-virtual-machine) 
is a quick way of doing that. 

For more information on configuring MBAM's use of XNAT, including further setup of the VVM XNAT, see 
[More Configuration Options](#more-configuration-options).


### 2. Celery, Redis, and Flower

Celery runs MBAM's asynchronous operations.  All communications with XNAT are asynchronous processes.  Redis is the 
message broker and results backend for Celery. In the local development environment, the MBAM start package runs both a 
Redis server instance and a Celery worker with the commands

    redis-server

and

    celery -A cookiecutter_mbam.run_celery:celery worker --pool=gevent --concurrency=500 --loglevel info

respectively.

During development you may be interested in using Flower to monitor your Celery process.

Run

    flower -A cookiecutter_mbam.run_celery:celery --port=5555

and visit http://0.0.0.0:5555.


### 3. AWS

- ##### Parameter Store  
    MBAM uses the AWS Parameter Store as a credential server for trusted developers. 

- ##### S3  
    User files are stored on s3 as well as on the Columbia servers.  s3 is the host of the images that users see.  If
    you are a trusted user, your images will be uploaded to the `mbam-test-sp` bucket in the MBAM s3 account.  If you're 
    testing and would like to check that your files were uploaded, contact MBAM developer Spiro Pantazatos for 
    credentials to login to s3.  
    
    If you are not a trusted user, you need to set up your own s3 bucket at https://aws.amazon.com/s3.  This requires 
    setting some [custom configuration](#1-custom-configuration-with-config-overrride) for your 
    [s3 bucket](#2-s3-configuration).
      
    S3 also stores the Cloud Formation templates that are used to build the site for deployment on AWS servers.  
    
- ##### Cloudfront  
    Cloudfront 



## Contributing

### 1. Process

Thank you for contributing to MBAM!  To contribute, please pull the latest version of the `development` branch and make 
a branch off of it.

When you have finished your feature or bug fix, first checkout development, pull any changes from the remote, and merge 
those changes into your local branches.  Be sure to resolve any merge conflicts.  Once you have an unconflicted branch, 
commit your work and test your branch following the steps in the [Testing](#testing).  If your branch passes 
automated and manual tests, open a PR and request review.  You should have at least one reviewer who did not contribute 
to the development of your branch.

### 2. What else you need

You need a [Docker installation](https://docs.docker.com/install/), either on your own computer, a remote host, or both.

If you plan to make changes to database schema in your contribution than SQLite won't work when generating migration 
files.  You need MySQL.

As already mentioned, new developers to the project who don't have access to MBAM credentials need their own XNAT
instance and S3 bucket.  


## More Setup and Configuration Options

### 1. Custom configuration with config overrride

For ephemeral or idiosyncratic configuration during development use `config/config.override.yml`.  Choose the name of 
the config you are using, for example, `TRUSTED`, and enter your custom variables in the block underneath.  An example:

    TRUSTED:
        CLAUDIAS_CUSTOM_VARIABLE_1: foo
        CLAUDIAS_CUSTOM_VARIABLE_2: 5

### 2. S3 configuration

If you're not a trusted user, s3 is one aspect of your MBAM setup that needs to be configured with config override.  
An example:

    LOCAL:
        S3_KEY_ID: <my_key_id>
        S3_SECRET_KEY: <my_secret_key>
        S3_BUCKET: <my_bucket>  

     

### 3. XNAT configuration

#### Configuration variables

MBAM needs to know five things about any XNAT version: the XNAT host, XNAT user, XNAT password, DICOM to NIFTI command 
ID, and the Freesurfer recon command ID.  If you want to change the default you must take an additional step to tell 
MBAM your XNAT configuration.  You have a couple of options.

1) Invoke the project's start utility directly to switch to backup XNAT.  This calls the same functions to run the
project as `npm start`.  First run `. env.sh` if you are not already in the MBAM virtual environment, and then 
`mbam run -h` will give you a full list of arguments.  The `--xnat` optional argument passed with `mbam run` will let 
you switch XNATs. Right now there are only three values this parameter can take, `mind`, `backup`, and `vvm`. `mind` 
is the default.

2) Another option is to use `config/config.override.yml`. Here is an example override file:


    TRUSTED:
        XNAT: FRED
        FRED_XNAT_HOST: https://my_url.net
        FRED_DICOM_TO_NIFTI_COMMAND: 2
        FRED_FREESURFER_RECON_COMMAND: 3
        
You would also put your username and password for your alternative XNAT in `config/secrets.yml`.  There you don't need 
the config name header.  Just add:

    FRED_XNAT_USER: Alice
    FRED_XNAT_PASSWORD: my-533krit-pa55w0rd
    
#### Setting up the VVM - preliminaries

If you are running the XNAT VVM on your local machine you have a couple more steps to take. 

After following the 
[instructions](https://wiki.xnat.org/documentation/getting-started-with-xnat/running-xnat-in-a-vagrant-virtual-machine) 
for installation, if you haven't already done so navigate to 
`{XNAT installation folder}/xnat-vagrant/configs/xnat-release` and run 

    vagrant up
    
When you try to navigate to http://10.1.1.17 you may see a bad gateway error.  If you do, from the same directory run:

    vagrant ssh
    sudo service tomcat7 restart
    
and give it a few minutes.

After you've succeeded in loading the XNAT instance, log in with username and password `admin`.  You may now experience
an extremely repetitive timeout message that kicks you out.  This writer knows one way to deal with this.  At
the command prompt of the virtual machine, run

    sudo timedatectl set-ntp no
    sudo timedatectl set-time "2020-03-01 14:56:00"
    sudo timedatectl set-ntp on
    
 Substitute the current date and time of course.
 
 #### Setting up the VVM or any other XNAT instance - Docker images and commands
 
 ##### a. Make XNAT communicate with Docker 
After you have a working XNAT instance, it needs to be pointed to two containers on a Docker host, the DICOM to NIFTI 
conversion container and the Freesurfer recon container.  For testing, you probably also want the mock Freesurfer 
 container.
  
Out of the box, XNAT communicates with `unix:///var/run/docker.sock`. You can either build your Docker containers on the 
same machine as the XNAT host, in which case you can leave that be, or a different machine, in which case you must 
change it to the host and port your Docker daemon is listening on.

If you're using the VVM XNAT and you'd like to use your computer as the Docker host, you need to do two things:

- expose the port Docker is listening on, like so:

    `socat TCP-LISTEN:2376,reuseaddr,fork,bind=127.0.0.1 UNIX-CLIENT:/var/run/docker.sock`

- Edit "Container Server Host" in XNAT by navigating to Administer->Plugin Settings->Container Server Setup and 
clicking edit.  Change the URL to the URL of your Docker host.  If you are using the VVM to host XNAT and your computer
to host Docker, your computer's URL from the point of view of the VVM is http://10.0.2.2:2376 

 To find this setting in XNAT, you navigate to Administer->Plugin Settings->Container Server Setup.
 
 ##### b. Build containers
 
 The DICOM to NIFTI container is stored in `mbam/pipelines/dcm2niix/dcm2niix-xfer`.  To build the container, navigate to
 cd into this directory and run `docker build . -t dcm2nii-xfer`.  You should see a Docker image appear under Administer
 -> Tools -> Plugin Settings -> Images and Commands.  If you don't, scroll down to the bottom of ths page and see if 
 any images are hidden.  Click on the eye to unhide them if so.  Similarly, cd into `mbam/pipelines/freesurfer/freesurfer-recon-xfer`
 and build with the analogous command.  Now you need to add the command (a JSON file the XNAT container service uses to
 configure the Docker container when it launches it.  For both DICOM to NIFTI and Freesurfer recon, this file is stored 
 as `command.json` in the same directory with the `Dockerfile`.  For DICOM to NFIT, copy the 
 text of this file, navigate to Administer -> Tools -> Plugin Settings -> Images and Commands, click on Add New Command
 next to the DICOM to NIFTI image, and paste the command into the text box, and click Save Command.) Then do the same 
 for Freesurfer recon.  
 
 Note that MBAM is configured so that by default it assumes you are a trusted developer; however, if you are not its 
 backup defaults, if you will, assume that XNAT is running in the Vagrant Virtual Machine.  If you add the DICOM to 
 NIFTI first, and Freesurfer recon second, MBAM will be correctly configured with their XNAT command numbers 1 and 2. 
 (It is also configured with the default host, username, and password for VVM XNAT.) If you wind up changing any of 
 this, or experimenting with these commands during development so that their number in your VVM XNAT increments, 
 you'll need to make sure your local MBAM points to the right command with [config override](#1-custom-configuration-with-config-overrride).
 

### 4. Database setup

There are two ways to use MySQL with MBAM, either using the application installed on your 
machine or using the dockerized version.

A note to preemptively explain errors: if you ever install dockerized MySQL, the MBAM application seems to find and 
connect to it at times when you think it shouldn't.  If you intend to connect to different database, make sure your 
MySQL Docker container is not running. 
 

#### MySQL Installation

Install a recent version of MySQL. (As of this writing, the current version is 8.0).  If on MacOS, do this with

    brew install mysql

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

#### Dockerized MySQL

Run the following command from the `build/docker` directory:

    docker-compose up -d mysql 


## Testing

### 1. Run automated tests in the local development environment

From the mbam top level directory run:

    mbam test
    
This will run all tests.  This command is a wrapper for Pytest, more specifically for the command 
    
    pytest ./tests --verbose
    
You can subsitute any other pytest command with 

    mbam run -c <command>
    
For example, 

    mbam run -c pytest ./tests --verbose
    
is equivalent to `mbam run`.  Using the MBAM start package will ensure the correct configuration of tests. 


### 2.  Run automated tests in the docker environment

MBAM must be dockerized to be deployed on Amazon servers.  To run MBAM's test in the docker environment, run

    mbam test --docker
    
This command is a wrapper for 

    docker-compose build && docker-compose -f test.yml up

### 3. Test that migrations work

If you've made changes to any of the MBAM models, you should test that you are committing a series of migration files 
that are continuous with the migration files in the latest version of development, that run without error, and that 
bring a new database up-to-date with your current models.

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

As of this writing, an MBAM user should be able to upload up to 3 scans at a time.  Those files can be in one of three 
formats: a .zip file of DICOMS, an uncompressed NIFTI file (.nii) and a compressed NIFTI file (.nii.gz).  A user's 
uploaded files should be saved both to an S3 bucket and to an XNAT instance.

Upon upload, MBAM should automatically convert DICOM files to NIFTI, if applicable, and then kick off the Freesurfer 
reconstruction process, which runs in a Docker container also hosted on a Columbia server.  At the end of this process 
MBAM should transfer the output files from the Docker container to XNAT and S3.  The MBAM database should be updated 
with the S3 and XNAT locations of the original uploaded scan, the NIFTI files (but only if a conversion was performed), 
and the Freesurfer output.

Because Freesurfer reconstruction is a many-hour process in the best case, for testing purposes it is best to use a mock 
Freesurfer container that provides output as if Freesurfer ran.  If you are a trusted developer, you can make MBAM use 
this mock container by setting 

    TRUSTED:
        FREESURFER_RECON_COMMAND: 38 
        
in `mbam/config/config.override.yml`. 

If you're not a trusted developer you can set up 

[UNFINISHED]


#### Setting up the XNAT container service for testing

If you are a trusted user, by default your MBAM development server is configured to access DICOM to NIFTI conversion and 
Freesurfer recon containers on MIND XNAT.  If you would like to switch to the mock Freesurfer container for manual 
testing, 


[UNFINISHED]


## Resources

1. XNAT

For more information about XNAT you may be interested in visiting 
[the documentation](https://wiki.xnat.org/documentation).

For developing an intuitive sense of the XNAT container service, an interface to the Docker daemon MBAM uses to launch
Docker containers, you may be interested in working through 
[this tutorial](https://github.com/MIND-NYSPI/xnat-cs-tutorial/blob/master/tutorial.md), written by one of the MBAM
developers, Katie Surrence.  You may find it more user friendly than the XNAT docs.  
 
    


    

 
   