#!/usr/bin/env bash
cd `dirname "$0"`
version=1
docker build \
 -t tomsaleeba/natcap-invest-docker-flask:3.4.2-$version \
 -t tomsaleeba/natcap-invest-docker-flask:latest \
 .
