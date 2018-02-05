#!/usr/bin/env bash
cd `dirname "$0"`

curl -X POST \
  --data @../natcap_invest_docker_flask/static/example-farm-vector.json \
  -H 'Content-type: application/json' \
  http://localhost:5000/pollination
