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
(on my system had to 
$ rm /usr/lib/x86_64-linux-gnu/libxml2.so.2
$ ln -s /opt/anaconda/lib/libxml2.so.2.9.2 ./libxml2.so.2

Edit settings.py
---> change DB_USER to 'mbam'

Now run the migrate command to make the mbam tables (muser and scan)
$ python manage.py db upgrade

In MySQL brain_db database there should now be all required tables 

Now can start the application using
$ python manage.py runserver
