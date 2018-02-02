""" run this module with no args: python -m natcap_invest_docker_flask """
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from natcap_invest_docker_flask import make_app, natcap_wrapper

app = make_app(natcap_wrapper.NatcapModelRunner())
app.run(host='0.0.0.0', debug=True)
