#!/bin/bash

proc=$1

cp ./build/docker/web/Dockerfile .

if [ "$proc" == "test" ]; then
    sudo /etc/init.d/apache2 stop
    sudo service mysql stop
    cd build/docker
    docker-compose up -d web
    sleep 5
elif [ "$proc" == "spiro" ]; then
    rsync -e "ssh -o StrictHostKeyChecking=no" -rPz ~/mbam/ spiropan@50.116.25.254:~/mbam/
    ssh spiropan@50.116.25.254 -t "cd mbam && docker-compose build && docker-compose up -d && docker image prune -a -f && exit"
else
    echo hello
fi





