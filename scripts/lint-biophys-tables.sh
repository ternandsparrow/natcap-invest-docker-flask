#!/bin/bash
# check biophysical LULC code tables for errors
set -euo pipefail
cd `dirname "$0"`/..

# check for unique lucode column values
for curr in $(ls docker/landcover_biophysical_table/*.csv); do
  if cat $curr | cut -f 1 -d ',' | sort | uniq -c | grep -v '^      1'; then
    echo "$curr FAIL, found duplicate lucode value"
    exit 1
  else
    echo "$curr OK"
  fi
done
