#!/usr/bin/env bash
cd `dirname "$0"`
version=1
which nose2 > /dev/null
rc=$?
set -e
if [ "$rc" != "0" ]; then
  echo '[ERROR] nose2 command not found, run: pip install -r requirements-test.txt'
  exit $rc
fi
nose2
docker build \
 -t tomsaleeba/natcap-invest-docker-flask:3.4.2-$version \
 -t tomsaleeba/natcap-invest-docker-flask:latest \
 .
