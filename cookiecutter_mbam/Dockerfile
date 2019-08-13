FROM python:3

# Install node and npm
RUN apt-get install -y curl \
&& curl -sL https://deb.nodesource.com/setup_10.x | bash - \
&& apt-get install -y nodejs \
&& curl -L https://www.npmjs.com/install.sh | sh
RUN ["apt-get", "install", "-y", "vim"]

# Install pipenv
RUN ["pip","install","pipenv"]

# Specify work directory
WORKDIR /app

# Copy files needed for the pipenv install
COPY Pipfile Pipfile.lock /app/
RUN ["pipenv","install","--dev","--system","--deploy"] # install the app and dep

# Copy files needed for the npm install
COPY package.json package-lock.json webpack.config.js /app/
RUN ["npm","install"] # install node modules

# Copy rest of files
COPY . /app
RUN ["npm", "run","build"] # build assets with webpack
