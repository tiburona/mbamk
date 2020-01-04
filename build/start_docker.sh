#!/bin/bash


env=$1

cp -r ./build/docker/* .

cp ./build/docker/web/Dockerfile .

if [ "$env" == "test" ]; then
    sudo /etc/init.d/apache2 stop
    sudo service mysql stop
    docker-compose up -d web
    sleep 5
elif [ "$env" == "server" ]; then
    echo "$env"
else
    echo hello
fi

#dockerDirs=(jatos mysql nginx web)
#for dir in "${dockerDirs[@]}"
#do
#    rm -rf ./"${dir}"
#done
#
#
#rm ./docker-compose*yml
#rm ./test.yml
#rm ./Dockerfile




