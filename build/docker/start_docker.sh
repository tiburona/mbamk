#!/bin/bash

env=$1

cp ./build/docker/web/Dockerfile .

if [ "$env" == "test" ]; then
    sudo /etc/init.d/apache2 stop
    sudo service mysql stop
    cd build/docker
    docker-compose up -d web
    sleep 5
elif [ "$env" == "server" ]; then
    echo "$env"
else
    echo hello
fi





