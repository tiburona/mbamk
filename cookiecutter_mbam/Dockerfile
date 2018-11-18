# -- From https://github.com/pypa/pipenv/blob/master/Dockerfile
#FROM kennethreitz/pipenv
FROM python:3

COPY . /app

WORKDIR /app/cookiecutter_mbam/

RUN pip install pipenv

# -- Replace with the correct path to your app's main executable
# -- From cookiecutter auto docs for starting app in production mode
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV DATABASE_URL="mysql+pymysql://mbam:mbam123@mysql/brain_db"

# Install node and npm
RUN apt-get install -y curl \
&& curl -sL https://deb.nodesource.com/setup_10.x | bash - \
&& apt-get install -y nodejs \
&& curl -L https://www.npmjs.com/install.sh | sh

# Install the Flask App dependencies
RUN ["pipenv","install","--system","--deploy"]
# Install node modeuls
RUN ["npm","install"]

RUN ["npm", "run","build"] # build assets with webpack
#RUN ["flask", "run"] # start the flask server
