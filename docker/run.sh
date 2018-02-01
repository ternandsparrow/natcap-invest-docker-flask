#!/usr/bin/env bash
cd `dirname "$0"`
# FIXME only for dev, make prod ready by using uwsgi or similar
python -m natcap_invest_docker_flask
