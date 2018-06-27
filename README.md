First step is deploy the flask app from github repo. 

$ git clone https://github.com/spiropan/flask_brain_db

Clone this repo to your local machine. In the top level directory, create a virtual environment:
$ virtualenv venv
$ source venv/bin/activate

Now install the required modules:
$ pip install -r requirements.txt

Download and install Jatos from https://github.com/JATOS/JATOS/releases
Unzip and cd into folder (i.e. jatos-2.2.4_linux_java).
Modify the conf/production.conf file to include:

"#Database configuration - MySQL database"
db.default.url="jdbc:mysql://localhost/brain_db?characterEncoding=UTF-8"
db.default.username='mbam'
db.default.driver=com.mysql.jdbc.Driver
jpa.default=mysqlPersistenceUnit

Create the MySQL database and user specificed above
$ mysql -u root -p
-> create database brain_db;
-> create user 'mbam'@localhost identified by '';
-> grant all on brain_db.* to 'mbam'

Start the MySQL server
$ sudo service mysql start

This should initialize the database 'brain_db' and the tables generated by jatos program
$ ./loader.sh start

Run the migrate command to create the rest of the tables. 
(on my linux Ubuntu system I had to:
$ rm /usr/lib/x86_64-linux-gnu/libxml2.so.2
$ ln -s /opt/anaconda/lib/libxml2.so.2.9.2 ./libxml2.so.2

On my Mac OS X I had to:
brew install libxml2
brew link --force libxml2

Edit settings.py
---> change DB_USER to 'mbam'

Now run the migrate command to make the mbam tables (muser and scan)
$ python manage.py db upgrade

In MySQL brain_db database there should now be all required tables 
If above doesn't work then can run below (or maybe only need the below). 
$ python manage.py shell
>> import db
>> dp.create_all()

Now can start the application using
$ python manage.py runserver


# To run on local MAC OSX and get mail to work follow these instructions
http://www.developerfiles.com/how-to-send-emails-from-localhost-mac-os-x-el-capitan/

#############################################################################
# Common error messages and short term fixes:
1) sqlalchemy.exc.InternalError: (pymysql.err.InternalError) (1050, u"Table 'role' already exists") [SQL: u'\nCREATE TABLE `role` (\n\tid INTEGER NOT NULL AUTO_INCREMENT, \n\tname VARCHAR(80), \n\tdescription VARCHAR(255), \n\tPRIMARY KEY (id), \n\tUNIQUE (name)\n)\n\n']

BELOW MYSQL COMMAND WILL FIX ABOVE ERROR MESSAGE:
INSERT INTO alembic_version (version_num) VALUES ('a78d98748544');

2) nginx_1  | 2017/09/15 19:24:16 [error] 5#5: *1 open() "/usr/src/app/flask_brain_db/static/papaya/build/papaya.css" failed (2: No such file or directory), client: 79.129.130.214, server: dev.mybrainandme.org, request: "GET /static/papaya/build/papaya.css HTTP/1.1", host: "dev.mybrainandme.org", referrer: "https://dev.mybrainandme.org/"

TO FIX THIS BE SURE TO BIND MAP (OR LATER COPY FILES IN THE DOCKERFILE) FROM ./web/flask_brain_db/static:/usr/src/app/flask_brain_db/static ONLY UNDER THE
NGINX SERVICE, AND *NOT* UNDER THE WEB SERVICE

3) For now to switch between production and staging need to uncomment line in the nginx/Dockerfile. Is there a better solution??

4) To add SSL to new server must run the four lines of code from the 'deployment_notes.md' to run letsencrypt. Is there a way to add an automation script that will check for 
a certificate, and if not available install, or if expired, renew?

5) Automate setting up SMTP on the new Digital Ocean Droplet's? Follow below links:
https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postfix-as-a-send-only-smtp-server-on-ubuntu-14-04
https://accounts.google.com/b/0/DisplayUnlockCaptcha

Here if on Linode and using GMAIL:
https://www.linode.com/docs/email/postfix/configure-postfix-to-send-mail-using-gmail-and-google-apps-on-debian-or-ubuntu/

App password is saved in mbaminfo Drive file called Important Info

6) Set up .htpasswd to restict access to the development site:
https://www.digitalocean.com/community/tutorials/how-to-set-up-password-authentication-with-nginx-on-ubuntu-14-04


Useful tool to convert MySQL tables to SQLAlchemy code: 
sqacodegen. I used this to easily model the Jatos (v2 and v3) database in SQLAlchemy. 
https://pypi.python.org/pypi/sqlacodegen

#Commands to provision DO droplet using docker-machine:
$ docker-machine create --driver=digitalocean --digitalocean-access-token=$DO_TOKEN --digitalocean-size=1gb blog

To create user and add to sudoers follow:
https://www.digitalocean.com/community/tutorials/how-to-create-a-sudo-user-on-ubuntu-quickstart

To set up SSH keys on docker-machine provisioned DO droplets follow:
Add the public keys from MacBook Air (id_rsa.pub) and from home computer (do_key_public) to the authorized_keys in each DO droplet
https://askubuntu.com/questions/466549/bash-home-user-ssh-authorized-keys-no-such-file-or-directory


https://askubuntu.com/questions/466549/bash-home-user-ssh-authorized-keys-no-such-file-or-directory


To set up separate MySQL DO Droplet follow:
https://www.digitalocean.com/community/tutorials/how-to-set-up-a-remote-database-to-optimize-site-performance-with-mysql



