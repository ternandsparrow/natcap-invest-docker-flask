#!/usr/bin/env bash
set -e
cd `dirname "$0"`
apt-get update

data_dir=/data/pollination

function get_raster {
  our_dir=/tmp/foo
  mkdir $our_dir
  pushd $our_dir
  raster_archive=$our_dir/raster.zip
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
  pushd $data_dir
  rm -rf *
  popd
  theArchive=$data_dir/south_australia_landcover.tif.gz
  mv *.tif.gz $theArchive
  if [ ! -f $theArchive ]; then
    echo "[ERROR] expected $theArchive to be present and it wasn't"
    exit 1
  fi
  popd
}

apt-get --assume-yes install \
  unzip \
  wget
get_raster &

apt-get --assume-yes install \
  gdal-bin \
  python-pip \
  python-setuptools \
  python-dev \
  gcc \
  optipng

pip install -r requirements.txt
wait

mv *.csv $data_dir
rm -r /workspace/pollination/
apt-get --assume-yes purge \
  python-pip \
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
