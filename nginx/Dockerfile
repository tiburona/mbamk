#FROM nginx:1.11.3
FROM nginx:1.14.2
RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/
RUN rm  /etc/nginx/conf.d/default.conf
# Make sure to define NGINX_CONFIG_FILE in .env file, and/or
# can also define default by setting =value it here.
ARG NGINX_CONFIG_FILE
COPY $NGINX_CONFIG_FILE /etc/nginx/conf.d/
COPY .htpasswd /etc/nginx/

# The below is so that we can change nginx settings on the fly and debug
# using vim within the shell but eventually want to take out since it increases
# build time.
RUN ["apt-get", "update"]
RUN ["apt-get", "install", "-y", "vim"]
