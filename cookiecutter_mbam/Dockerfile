FROM python:3

COPY . /app

# Replace .env with a file for dockerized version of flask app
COPY .docker_env /app/cookiecutter_mbam/.env
WORKDIR /app

# Install node and npm
RUN apt-get install -y curl \
&& curl -sL https://deb.nodesource.com/setup_10.x | bash - \
&& apt-get install -y nodejs \
&& curl -L https://www.npmjs.com/install.sh | sh

RUN ["pip","install","pipenv"]
RUN ["pipenv","install","--system","--deploy"] # install the app and dep
RUN ["npm","install"] # install node modules
RUN ["npm", "run","build"] # build assets with webpack
