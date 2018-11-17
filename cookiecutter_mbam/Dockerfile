# -- From https://github.com/pypa/pipenv/blob/master/Dockerfile
FROM kennethreitz/pipenv

COPY . /app

WORKDIR /app/mbam/cookiecutter_mbam/

# -- Replace with the correct path to your app's main executable
# -- From cookiecutter auto docs for starting app in production mode
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
#ENV DATABASE_URL="<YOUR DATABASE URL>"

RUN ["npm", "run","build"] # build assets with webpack
RUN ["flask", "run"] # start the flask server
