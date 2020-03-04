#!/usr/bin/env bash
# entrypoint for the Docker container
set -euo pipefail
cd `dirname "$0"`/..

echo "[INFO] running for env=${NIDF_ENV:?set to 'development' or 'production'}"
: ${SOCKETIO_SECRET:?set to some obscure value}

python3.7 natcap_invest_docker_flask/main.py
