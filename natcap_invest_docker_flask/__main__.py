"""
run this module with flask:
    cd natcap-invest-docker-flask
    export FLASK_APP=natcap_invest_docker_flask
    export FLASK_ENV=development
    flask run --host 0.0.0.0

...or use a WSGI server to run the app for production.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from natcap_invest_docker_flask import make_app, natcap_wrapper

app = make_app(natcap_wrapper.NatcapModelRunner())
