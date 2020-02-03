#!/bin/bash

export PYTHONPATH=${PYTHONPATH}:${PWD}/tools

if [ "$1" == "install" ]; then
    python3 -m pip install -e ./tools/start
fi

pipenv shell