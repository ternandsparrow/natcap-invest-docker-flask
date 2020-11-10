#!/usr/bin/env bash
set -euxo pipefail
cd `dirname "$0"`/../..

apt update
apt dist-upgrade --assume-yes

# assumes the base image also uses this path
data_dir=/data/pollination

function get_raster {
  our_dir=$(mktemp --directory)
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

get_raster &

apt-get --assume-yes --no-install-recommends install \
  gdal-bin \
  netbase \
  optipng

pip3 install -r requirements.txt
pip3 freeze > pip.freeze
wait

rm -r /workspace/pollination/

apt-get --assume-yes autoremove
apt-get --assume-yes clean
rm -rf \
  /var/lib/apt/lists/* \
  /tmp/* \
  /var/tmp/*
