import os
import logging

from flask import Flask, jsonify, render_template, request
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

MAX_YEARS_TO_SIMULATE = 30
crop_type_key = 'crop_type'


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


class InvalidUsage(Exception):
    """ from http://flask.pocoo.org/docs/1.0/patterns/apierrors/ """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def make_app(model_runner):
    app = Flask(__name__)
    CORS(app)
    # stop Jinja2/angularjs conflict, thanks
    # https://stackoverflow.com/a/30362956/1410035
    jinja_options = app.jinja_options.copy()

    jinja_options.update(
        dict(
            variable_start_string='{j{',
            variable_end_string='}j}',
        ))
    app.jinja_options = jinja_options
    app_root = os.path.dirname(os.path.abspath(__file__))
    app_static = os.path.join(app_root, 'static')

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.route('/')
    def root():
        return jsonify({
            '_links': [{
                'rel': 'pollination',
                'href': '/pollination'
            }, {
                'rel': 'tester-ui',
                'href': '/tester'
            }]
        })

    @app.route('/pollination', methods=['POST'])
    @accept('application/json')
    def pollination():
        """ executes the InVEST pollination model and returns the results """
        if not request.is_json:
            raise InvalidUsage("POST body doesn't look like JSON", 415)
        post_body = request.get_json()
        validate_request(post_body)
        years_to_simulate = post_body['years']
        if years_to_simulate > MAX_YEARS_TO_SIMULATE:
            raise InvalidUsage('years param cannot be any larger than %d' %
                               MAX_YEARS_TO_SIMULATE)
        geojson_farm_vector = post_body['farm']
        # TODO validate farm vector is within extent of landcover raster
        log_geojson(geojson_farm_vector, 'farm')
        geojson_reveg_vector = post_body['reveg']
        # TODO validate the reveg vector is in an appropriate location compared
        # with the farm. Probably within a few kms is good enough
        log_geojson(geojson_reveg_vector, 'reveg')
        crop_type = post_body[crop_type_key]
        result = model_runner.execute_model(geojson_farm_vector,
                                            years_to_simulate,
                                            geojson_reveg_vector, crop_type)
        return jsonify(result)

    def validate_request(request_dict):
        try:
            required_keys = ['years', crop_type_key, 'farm', 'reveg']
            for curr in required_keys:
                request_dict[curr]
        except KeyError:
            raise InvalidUsage('POST body must have the keys: ' +
                               str(required_keys))
        valid_crop_types = ['apple', 'canola', 'lucerne']
        if not request_dict[crop_type_key] in valid_crop_types:
            raise InvalidUsage('crop_type must be one of: ' +
                               str(valid_crop_types))
        assert_geojson(request_dict['farm'])
        assert_geojson(request_dict['reveg'])
        assert_json_schema()

    def assert_json_schema():
        class JsonInputs(Inputs):
            json = [JsonSchema(schema=pollination_schema)]

        inputs = JsonInputs(request)
        if inputs.validate():
            return
        logger.debug('validation errors=%s' % inputs.errors)
        raise InvalidUsage('JSON schema validation failed: ' +
                           str(inputs.errors))

    def assert_geojson(geojson_dict):
        try:
            geojson.loads(dumps(geojson_dict))
        except ValueError as e:
            raise InvalidUsage('Not valid geojson: ' + e.message)

    @app.route('/tester')
    def tester():
        """ returns a UI for interacting with this service """
        example_farm_vector = read_example_json(
            os.path.join(app_static, 'example-farm-vector.json'))
        example_reveg_vector = read_example_json(
            os.path.join(app_static, 'example-reveg-vector.json'))
        return render_template('testerui.html',
                               example_farm_vector=example_farm_vector,
                               example_reveg_vector=example_reveg_vector,
                               url_root=request.url_root)

    return app
