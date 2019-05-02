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
MAX_YEARS_TO_SIMULATE = 30

def log_geojson(data, type_of_vector):
    data_str = dumps(data)
    if len(data_str) > 30:
        msg = data_str[:30] + '...'
    else:
        msg = data_str
    logger.debug('supplied %s GeoJSON=%s' % (type_of_vector, msg))


def read_example_json(file_path):
    with open(file_path) as f:
        with_newlines = f.read()
        result = with_newlines.replace('\n', '\\n')
        return result


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
        years_to_simulate = request.args.get('years', default=DEFAULT_YEARS_TO_SIMULATE, type=int)
        if years_to_simulate > MAX_YEARS_TO_SIMULATE:
            response_body = {'message':'years param cannot be any larger than %d' % MAX_YEARS_TO_SIMULATE}
            return (jsonify(response_body), 400, {'Content-type': 'application/json'})
        post_body = request.get_json()
        validation_result = is_request_valid(post_body)
        if validation_result['failed']:
            return validation_result['response']
        geojson_farm_vector = post_body['farm']
        # TODO validate farm vector is within extent of landcover raster
        log_geojson(geojson_farm_vector, 'farm')
        geojson_reveg_vector = post_body['reveg']
        # TODO validate the reveg vector is in an appropriate location compared with the farm. Probably within a few kms is good enough
        log_geojson(geojson_reveg_vector, 'reveg')
        result = model_runner.execute_model(geojson_farm_vector, years_to_simulate, geojson_reveg_vector)
        return jsonify(result)


    def is_request_valid(request_dict):
        try:
            request_dict['farm']
            request_dict['reveg']
        except KeyError:
            return {'failed': True, 'response': abort(422)}
        farm_validation_result = is_valid_geojson(request_dict['farm'])
        if farm_validation_result['failed']: return farm_validation_result['response']
        reveg_validation_result = is_valid_geojson(request_dict['reveg'])
        if reveg_validation_result['failed']: return reveg_validation_result['response']
        schema_validation_result = do_json_schema_validation()
        if schema_validation_result['failed']: return schema_validation_result['response']
        return {'failed': False}


    def do_json_schema_validation():
        class JsonInputs(Inputs):
            json = [JsonSchema(schema=pollination_schema)]
        inputs = JsonInputs(request)
        if not inputs.validate():
            logger.debug('validation errors=%s' % inputs.errors)
            # TODO send inputs.errors in response
            return {'failed': True, 'response': abort(422)}
        return {'failed': False}


    def is_valid_geojson(geojson_dict):
        geojson_obj = geojson.loads(dumps(geojson_dict))
        is_geojson_obj_not_valid = not hasattr(geojson_obj, 'is_valid') or not geojson_obj.is_valid
        if is_geojson_obj_not_valid:
            # TODO send geojson_obj.errors() in response
            return {'failed': True, 'response': abort(422)}
        return {'failed': False}


    @app.route('/tester')
    def tester():
        """ returns a UI for interacting with this service """
        example_farm_vector = read_example_json(os.path.join(app_static, 'example-farm-vector.json'))
        example_reveg_vector = read_example_json(os.path.join(app_static, 'example-reveg-vector.json'))
        return render_template('testerui.html',
                example_farm_vector=example_farm_vector,
                example_reveg_vector=example_reveg_vector,
                url_root=request.url_root)


    return app


class SomethingFailedException(Exception):
  def __init__(self, http_resp):
    super(SomethingFailedException, self).__init__()
    self.http_resp = http_resp
