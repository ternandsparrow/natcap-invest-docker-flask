#!/usr/bin/env bash
set -e
cd `dirname "$0"`
apt-get update
# apt-get dist-upgrade # TODO might improve security

data_dir=/data/pollination
our_dir=/tmp/foo
raster_archive=$our_dir/raster.zip

function get_raster {
  mkdir $our_dir
  pushd $our_dir
  wget \
    -O $raster_archive \
    'https://github.com/tomsaleeba/landuse-raster-south-australia/releases/download/20180307-33m/landuse_raster_south_australia_33m_20180307.zip'
  unzip $raster_archive
  tif_count=`bash -c 'ls -1 *.tif | wc -l'`
  if [ "$tif_count" != "1" ]; then
    echo "[ERROR] expected exactly 1 .tif file, found $tif_count."
    exit 1
  fi
  gzip *.tif
  mv *.tif.gz $data_dir/south_australia_landcover.tif.gz
  popd
}

apt-get --assume-yes install \
  wget
get_raster &

apt-get --assume-yes install \
  gdal-bin \
  python-setuptools \
  python-dev \
  gcc \
  unzip

function install_deps {
  pip install -r requirements.txt
  pushd $data_dir
  rm -rf *
  popd
}

install_deps &
wait

mv *.csv $data_dir
apt-get --assume-yes purge \
  python-setuptools \
  python-dev \
  gcc \
  wget \
  unzip
apt-get --assume-yes autoremove
apt-get --assume-yes clean
rm -rf \
 /var/lib/apt/lists/* \
 /tmp/* \
 /var/tmp/*
rm setup.sh
