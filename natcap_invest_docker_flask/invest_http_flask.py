import os
import logging

from flask import Flask, jsonify, send_file, render_template, request, abort
from flask.json import dumps
from flask_accept import accept
from flask_cors import CORS
from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
import geojson

from .schema import schema as pollination_schema

logging.basicConfig()
logger = logging.getLogger('natcap_wrapper')
logger.setLevel(logging.DEBUG)

DEFAULT_YEARS_TO_SIMULATE = 3

def log_geojson(data):
    data_str = dumps(data)
    if len(data_str) > 30:
        msg = data_str[:30] + '...' 
    else:
        msg = data_str
    logger.debug('supplied GeoJSON=%s' % msg)

# FIXME can we create a class and pass this to the constructor?
def make_app(model_runner):
    app = Flask(__name__)
    CORS(app)
    # stop Jinja2/angularjs conflict, thanks https://stackoverflow.com/a/30362956/1410035
    jinja_options = app.jinja_options.copy()

    jinja_options.update(dict(
        variable_start_string='{j{',
        variable_end_string='}j}',
    ))
    app.jinja_options = jinja_options
    app_root = os.path.dirname(os.path.abspath(__file__))
    app_static = os.path.join(app_root, 'static')


    @app.route('/')
    def root():
        return jsonify({
            '_links': [
                {'rel': 'pollination', 'href': '/pollination'},
                {'rel': 'tester-ui', 'href': '/tester'}
            ]
        })


    @app.route('/pollination', methods=['POST'])
    @accept('application/json')
    def pollination():
        """ executes the InVEST pollination model and returns the results """
        if not request.is_json:
            abort(415)
        geojson_farm_vector = request.get_json()
        # TODO validate vector is within extent of landcover raster
        log_geojson(geojson_farm_vector)
        validation_result = is_schema_valid(geojson_farm_vector)
        if validation_result['failed']:
            return validation_result['response']
        years_to_simulate = request.args.get('years', default=DEFAULT_YEARS_TO_SIMULATE, type=int)
        geojson_reveg_vector = None # TODO make this a param
        result = model_runner.execute_model(geojson_farm_vector, years_to_simulate, geojson_reveg_vector)
        return jsonify(result)


    def is_schema_valid(geojson_string):
        # geojson validation
        feature_collection = geojson.loads(dumps(geojson_string))
        if not hasattr(feature_collection, 'is_valid') or not feature_collection.is_valid:
            # TODO send feature_collection.errors() in response
            return {'failed': True, 'response': abort(422)}
        # our own JSON schema validation
        class JsonInputs(Inputs):
            json = [JsonSchema(schema=pollination_schema)]
        inputs = JsonInputs(request)
        if not inputs.validate():
            logger.debug('validation errors=%s' % inputs.errors)
            # TODO send inputs.errors in response
            return {'failed': True, 'response': abort(422)}
        return {'failed': False}


    # FIXME handle double slashes
    @app.route('/image/<uniqueworkspace>/<imagename>')
    def get_png(uniqueworkspace, imagename):
        """ fetches the PNG version of a GeoTIFF in a lazy-init way """
        try:
            png_file_path = model_runner.get_png(uniqueworkspace, imagename)
            return send_file(png_file_path, mimetype='image/png')
        except SomethingFailedException as e:
            return e.http_resp


    # TODO add endpoint to retrieve GeoTIFF images


    @app.route('/tester')
    def tester():
        """ returns a UI for interacting with this service """
        example_farm_vector_path = os.path.join(app_static, 'example-farm-vector.json')
        with open(example_farm_vector_path) as f:
            with_newlines = f.read()
            example_farm_vector = with_newlines.replace('\n', '\\n')
        return render_template('testerui.html',
                example_farm_vector=example_farm_vector,
                url_root=request.url_root)


    return app


class SomethingFailedException(Exception):
  def __init__(self, http_resp):
    super(SomethingFailedException, self).__init__()
    self.http_resp = http_resp
