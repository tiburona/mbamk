https://ianlondon.github.io/blog/deploy-flask-docker-nginx/

https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-16-04

https://hub.docker.com/r/danriti/nginx-gunicorn-flask/~/dockerfile/

**https://medium.com/@pvs/containerized-micro-services-in-python-d140ea3f6420**

https://realpython.com/blog/python/dockerizing-flask-with-compose-and-machine-from-localhost-to-the-cloud/

https://hub.docker.com/r/laztoum/flask-gunicorn-nginx/

**http://www.patricksoftwareblog.com/how-to-use-docker-and-docker-compose-to-create-a-flask-application/**

https://www.digitalocean.com/community/tutorials/how-to-configure-a-continuous-integration-testing-environment-with-docker-and-docker-compose-on-ubuntu-14-04


To attach domain names to new name severs (i.e. at Digital Ocean) follow the below:

https://www.digitalocean.com/community/tutorials/how-to-set-up-a-host-name-with-digitalocean


To add Letsencrypt SSL to your server follow below link:

http://blog.nbellocam.me/2016/03/10/letsencrypt-and-nginx-on-docker/

Make sure to opn up port 443 first

$ iptables -A INPUT -p tcp -m tcp --dport 443 -j ACCEPT

$ sudo git clone https://github.com/letsencrypt/letsencrypt 

$ cd letsencrypt

$ sudo ./letsencrypt-auto certonly --standalone --renew-by-default --email spiropan@gmail.com -d www.mybrainandme.org -d mybrainandme.org

