#!/usr/bin/env python
"""
Let's face it, installing the dependencies for natcap is a pain.
This lets you run the server with a stub impl so you iterate quickly for dev work.

It's executable so just run it.
"""
import os
import sys
thisdir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import natcap_invest_docker_flask

class StubModelRunner(object):
    def execute_model(self, geojson_farm_vector):
        print('received farm vector=%s...' % str(geojson_farm_vector)[:30])
        return {
            'images': ['image1'],
            'records': [{'crop_type': 'stub1'}, {'crop_type': 'stub2'}]
        }


    def get_png(self, _, _2):
        return os.path.join(thisdir, 'onewhitepixel.png')


app = natcap_invest_docker_flask.make_app(StubModelRunner())
port = 5000
if len(sys.argv) > 1:
    val = sys.argv[1]
    try:
        port = int(val)
    except ValueError:
        print('Supplied port param "%s" is not a number, ignoring.' % val)
app.run(debug=True, port=port)
