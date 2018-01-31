#!/usr/bin/env bash
cd `dirname "$0"`
FLASK_APP=invest_http_flask.py flask run --host=0.0.0.0 # FIXME only for dev, make prod ready
