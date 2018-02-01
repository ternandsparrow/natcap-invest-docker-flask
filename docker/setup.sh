#!/usr/bin/env bash
set -e
cd `dirname "$0"`
pip install -r requirements.txt
apt-get update
apt-get --assume-yes install gdal-bin
apt-get --assume-yes clean
rm -rf \
 /var/lib/apt/lists/* \
 /tmp/* \
 /var/tmp/*
