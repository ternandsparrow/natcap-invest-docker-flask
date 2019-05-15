#!/usr/bin/env bash
cd `dirname "$0"`/..

theEnv=${NIDF_ENV:-development}
echo "[INFO] running for env=$theEnv"

if [ "$theEnv" == "development" ]; then
  export FLASK_APP=natcap_invest_docker_flask
  export FLASK_ENV=development
  flask run --host 0.0.0.0 $@
elif [ "$theEnv" == "production" ]; then
  cpuCount=`cat /proc/cpuinfo | grep processor | wc -l`
  maxYears=30
  expectedJobTime=10 # actually about 7 seconds, but add some padding
  timeout=`expr $maxYears \* $expectedJobTime / $cpuCount`
  echo "[INFO] setting gunicorn worker timeout to $timeout seconds"
  gunicorn \
    --workers ${GUNICORN_WORKER_COUNT:-2} \
    --bind 0.0.0.0:5000 \
    --timeout $timeout \
    $@ \
    natcap_invest_docker_flask.__main__:app
else
  echo "[ERROR] unknown NIDF_ENV value '$theEnv', cannot continue. Valid values are development, production."
  exit 1
fi
