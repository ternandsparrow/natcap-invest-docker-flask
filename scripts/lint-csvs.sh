#!/bin/bash
# check CSV tables for errors
set -euo pipefail
cd `dirname "$0"`/..

ignoreSampleData='grep -v -e almonds -e blueberries'

# Biophysical landuse code CSVs
## check for unique lucode column values
for curr in $(ls docker/landcover_biophysical_table/*.csv | $ignoreSampleData); do
  if cat $curr | cut -f 1 -d ',' | sort | uniq -c | grep -v '^      1'; then
    echo "$curr FAIL, found duplicate lucode value"
    exit 1
  else
    echo "$curr OK"
  fi
done


# Farm attribute tables
## only one data line per file
for curr in $(ls docker/farm_attribute_table/*.csv | $ignoreSampleData); do
 if wc -l $curr | grep -v '^2'; then
   echo "$curr FAIL, must only have 2 lines total (header and one data)"
   exit 1
 else
   # no lines means the count *is* 2
   echo "$curr OK"
 fi
done
