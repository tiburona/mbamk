FROM nginx:1.11.3
RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/
RUN rm  /etc/nginx/conf.d/default.conf
# Set default config file to be staging.conf.
# in production environment this should be overwritten in .env file
ARG NGINX_CONFIG_FILE=staging.conf
#COPY production_restricted.conf /etc/nginx/conf.d/
COPY $NGINX_CONFIG_FILE /etc/nginx/conf.d/
#COPY staging.conf /etc/nginx/conf.d/
COPY .htpasswd /etc/nginx/
