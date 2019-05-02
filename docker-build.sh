#!/usr/bin/env bash
cd `dirname "$0"`
version=1.1.0
which nose2 > /dev/null
rc=$?
set -e
if [ "$rc" != "0" ]; then
  echo '[ERROR] nose2 command not found, run: pip install -r requirements-test.txt'
  exit $rc
fi
nose2
docker build \
 -t ternandsparrow/natcap-invest-docker-flask:$version_3.6.0 \
 -t ternandsparrow/natcap-invest-docker-flask:latest \
 .
