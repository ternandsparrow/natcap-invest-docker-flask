#!/usr/bin/env bash
cd `dirname "$0"`/..

theEnv=${NIDF_ENV:-dev}
echo "[INFO] running for env=$theEnv"

if [ "$theEnv" == "development" ]; then
  export FLASK_APP=natcap_invest_docker_flask
  export FLASK_ENV=development
  flask run --host 0.0.0.0 $@
elif [ "$theEnv" == "production" ]; then
  gunicorn \
    --workers ${GUNICORN_WORKER_COUNT:-2} \
    --bind 0.0.0.0:5000 \
    $@ \
    natcap_invest_docker_flask.__main__:app
else
  echo "[ERROR] unknown NIDF_ENV value '$theEnv', cannot continue. Valid values are dev, prod."
  exit 1
fi
