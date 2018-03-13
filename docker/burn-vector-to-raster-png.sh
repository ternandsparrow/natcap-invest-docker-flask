#!/usr/bin/env bash
# performs the following
#   - copy the raster
#   - burn the vector into the cloned raster
#   - convert the burnt raster to PNG
set -e
srcRaster=$1
destPng=$2
srcVector=$3
srcVectorLayer=$4
burnValue=$5
if [ $# != 5 ]; then
  echo "[ERROR] expected exactly 5 arguments, got $#"
  echo "usage: $0 <src raster> <dest PNG> <src vector> <vector layer name> <burn value>"
  echo "   eg: $0 ./landcover.tif ./for-ui.png ./farm.shp farm_results 2000"
  exit 1
fi
# TODO more arg validation
clonedRaster=`bash -c "echo $destPng | sed 's/.png$/.tif/'"`
colourMapPath=`dirname "$0"`/raster-colour-map.txt
cp $srcRaster $clonedRaster
gdal_rasterize \
  -burn $burnValue \
  -l $srcVectorLayer \
  $srcVector \
  $clonedRaster
# TODO look at restricting the size in pixels
gdaldem \
  color-relief \
  $clonedRaster \
  $colourMapPath \
  $destPng \
  -of PNG
set +e
which optipng 2>&1 > /dev/null
OPTI_RC=$?
set -e
if [ $OPTI_RC == 0 ]; then
  optipng $destPng
fi
# don't delete intermediate .tif, we use the farm-only one to add the reveg
rm -f *.aux.xml
echo "[INFO] done, wrote result to $destPng"
