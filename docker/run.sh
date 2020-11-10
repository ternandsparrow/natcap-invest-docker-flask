#!/usr/bin/env bash
# entrypoint for the Docker container
set -euo pipefail
cd `dirname "$0"`/..

: ${SOCKETIO_SECRET:?set to some obscure value}
envName=${NIDF_ENV:?set to 'development' or 'production'}
echo "[INFO] running for env=$envName"

python natcap_invest_docker_flask/main.py
