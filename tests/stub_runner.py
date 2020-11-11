#!/usr/bin/env python
"""
Let's face it, installing the dependencies for natcap is a pain.
This lets you run the server with a stub impl so you iterate quickly for dev work.

It's executable so just run it.
"""
import natcap_invest_docker_flask
import os
import sys
import base64
thisdir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def get_base64_image_src_string(image_path):
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


class StubModelRunner(object):
    def execute_model(self, geojson_farm_vector, years_to_simulate,
                      geojson_reveg_vector, crop_type, mark_year_as_done_fn):
        print('received farm vector=%s...' % str(geojson_farm_vector)[:30])
        records = []
        for curr in range(1, years_to_simulate + 1):
            records.append({'crop_type': 'stub1', 'year': curr})
            records.append({'crop_type': 'stub2', 'year': curr})
        return {
            'images': {
                'base':
                get_base64_image_src_string(
                    os.path.join(thisdir, 'images', 'farm.png')),
                'reveg':
                get_base64_image_src_string(
                    os.path.join(thisdir, 'images', 'farm-and-reveg.png'))
            },
            'records': records
        }


app = natcap_invest_docker_flask.AppBuilder(StubModelRunner()).build()
port = 5000
if len(sys.argv) > 1:
    val = sys.argv[1]
    try:
        port = int(val)
    except ValueError:
        print('Supplied port param "%s" is not a number, ignoring.' % val)
app.run(debug=True, port=port)
