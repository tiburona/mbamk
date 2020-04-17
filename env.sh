#!/bin/bash

export PYTHONPATH=${PYTHONPATH}:${PWD}/tools

if [ "$1" == "install" ]; then
    pip install -e ./tools/start
fi

pipenv shell
