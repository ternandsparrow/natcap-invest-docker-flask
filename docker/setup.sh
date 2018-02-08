#!/usr/bin/env bash
set -e
cd `dirname "$0"`
apt-get update
apt-get --assume-yes install \
  gdal-bin \
  python-setuptools \
  python-dev \
  gcc
pip install -r requirements.txt
apt-get --assume-yes purge \
  python-setuptools \
  python-dev \
  gcc
apt-get --assume-yes autoremove
apt-get --assume-yes clean
rm -rf \
 /var/lib/apt/lists/* \
 /tmp/* \
 /var/tmp/*
rm setup.sh
