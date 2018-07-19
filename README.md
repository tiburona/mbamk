1. If you haven't already, the first step is to [install Docker](https://docs.docker.com/install/).

2. Clone this repository:

`$ git clone https://github.com/spiropan/mbam`

3. Install a local version of XNAT.  Instructions are [here](https://wiki.xnat.org/display/XNAT17/Running+XNAT+in+a+Vagrant+Virtual+Machine).  Use the one-line XNAT setup.  You will know it has worked when you can navigate to 10.1.1.17 in your browser and get an XNAT login page.  The login and password are both 'xnat', which of course you can change in your configuration if you wish.

4. You'll need an XNAT project.  Log in to your XNAT instance and go to **New -> Project**.  Fill out the values for Project Title, Running Title, and Project ID

5. There are two configuration files that should be placed in the top-level directory.  The first should be named `.env`.  It needs only the following line
`NGINX_CONFIG_FILE=local.conf`

The second is called `app_config.env`.

It should begin something like this:

```
SECRET_KEY=you-will-never-guess
DB_ROOT_PASSWORD=test
DB_HOST=mysql
DB_PASSWORD=mbam123
```

You can change the key and password values if you like; they are configuring a local database instance.   

`app_config.env` then continues:

```
XNAT_PROJECT=<project-id> # you created this project in step 4
XNAT_USER=admin # or <your-xnat-user> if you changed it
XNAT_PSWD=admin # or <your-password> if you changed it
XNAT_URL=10.1.1.7

RUN_FROM=local
```

6. Once those configuration files are in place, run

`$ docker-compose up -d mysql`

and finally

`$ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
