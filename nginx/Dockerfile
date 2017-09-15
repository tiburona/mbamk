FROM nginx:1.11.3
RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/
RUN rm  /etc/nginx/conf.d/default.conf
#COPY flask_brain_db.conf /etc/nginx/conf.d/
COPY staging.conf /etc/nginx/conf.d/
