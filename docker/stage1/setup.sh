#!/usr/bin/env bash
set -e
cd `dirname "$0"`/../..
apt-get update

data_dir=/data/pollination

function get_raster {
  our_dir=/tmp/foo
  mkdir $our_dir
  pushd $our_dir
  raster_archive=$our_dir/raster.zip
  wget \
    -O $raster_archive \
    'https://github.com/ternandsparrow/landuse-raster-south-australia/releases/download/20180307-33m/landuse_raster_south_australia_33m_20180307.zip'
  unzip $raster_archive
  tif_count=`bash -c 'ls -1 *.tif | wc -l'`
  if [ "$tif_count" != "1" ]; then
    echo "[ERROR] expected exactly 1 .tif file, found $tif_count."
    exit 1
  fi
  gzip *.tif
  rm -rf $data_dir/*
  theArchive=$data_dir/south_australia_landcover.tif.gz
  mv *.tif.gz $theArchive
  if [ ! -f $theArchive ]; then
    echo "[ERROR] expected $theArchive to be present and it wasn't"
    exit 1
  fi
  rm -rf $our_dir
  popd
}

apt-get --assume-yes --no-install-recommends install \
  unzip \
  wget

get_raster &

apt-get --assume-yes --no-install-recommends install \
  gdal-bin \
  python-pip \
  python-setuptools \
  python-dev \
  gcc \
  gunicorn \
  optipng

pip install -r requirements.txt
pip freeze > pip.freeze
wait

#mv *.csv $data_dir # FIXME change to CSV files in the subdirs
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
