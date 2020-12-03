#!/bin/bash
# Prepares the files required to run the official NatCap sample data through
# our framework.
set -euxo pipefail
cd `dirname "$0"`
thisDir=$PWD
cd ..

force=${1:-} # anything is truthy
flagFile=/tmp/prep-for-sample-done-done
if [ ! "$force" -a -f $flagFile ]; then
  exit 0
fi

farmShp=/data/pollination-sample/farms.shp

echo "Writing farm shapefile->geojson for UI"
ogr2ogr -f geojson /vsistdout/ $farmShp \
  | python3 $thisDir/parse-geojson-for-crop.py \
  > /data/pollination-sample/ui.json

lulcPath=/data/pollination-sample/landcover_biophysical_table.csv
tmpLulc=$lulcPath.filtered
echo "Filtering LULC table columns"
cut -d, -f2 --complement $lulcPath > $tmpLulc

# TODO: we should remove the columns for the season each crop does NOT use.
# Leaving them in won't break things but you'll see warnings about "no pixels"
# or something to that effect during the run.
for curr in almonds blueberries; do
  echo "$curr: guild table"
  ln --symbolic --force \
    /data/pollination-sample/guild_table.csv \
    ./docker/guild_table/$curr.csv
  ln --symbolic --force \
    ./docker/guild_table/$curr.csv \
    ./docker/guild_table/${curr}_varroa.csv
  echo "$curr: farm attributes"
  tmpFat=`mktemp`
  ogr2ogr -f csv /vsistdout/ $farmShp > $tmpFat
  rmCropType="cut -d, -f1 --complement"
  # write header
  head -n 1 $tmpFat | $rmCropType   > ./docker/farm_attribute_table/$curr.csv
  # write data rows
  grep $curr $tmpFat | $rmCropType >> ./docker/farm_attribute_table/$curr.csv
  echo "$curr: LULC table"
  ln --symbolic --force \
    $tmpLulc ./docker/landcover_biophysical_table/$curr.csv
done

echo $(date) > $flagFile
