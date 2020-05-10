#!/usr/bin/env bash
priv_reg=10.20.193.32:5000

docker build . -t ${priv_reg}/mbam/fs2mesh:latest
docker push ${priv_reg}/mbam/fs2mesh:latest

