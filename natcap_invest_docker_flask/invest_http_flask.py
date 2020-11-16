import os
import math
import multiprocessing

from flask import Flask, jsonify, render_template, request, Response
from flask.json import loads, dumps
from flask_accept import accept
from flask_cors import CORS
from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
import geojson

from natcap_invest_docker_flask.schema import schema as pollination_schema
from natcap_invest_docker_flask.logger import logger_getter
import reveg_alg.plot

logger = logger_getter.get_app_logger()

MAX_YEARS_TO_SIMULATE = 30
crop_type_key = 'crop_type'

app_root = os.path.dirname(os.path.abspath(__file__))
app_static = os.path.join(app_root, 'static')


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


def estimate_runtime():
    """ Estimate how long a simulation will take for the given number of
    years on the current machine (CPU dependent) """
    cpu_count = multiprocessing.cpu_count()
    years = request.args.get('years', type=int)
    if not years:
        raise InvalidUsage(
            "The 'years' param is required and must be an integer >= 1")
    time_per_year = 4  # seconds
    diluted_cpu_effect = 1 + (1.0 * cpu_count / 10)
    raw_guess = time_per_year * math.ceil(1.0 * years / diluted_cpu_effect)
    result = int(max(raw_guess, 15))
    return jsonify({'seconds': result})


def reveg_curve_png():
    years = request.args.get('years', default=15, type=int)
    max_years_limit = 50
    if not years or years > max_years_limit:
        raise InvalidUsage("The 'years' param, if supplied, must be " +
                           "an integer >= 1 && <= %d" % max_years_limit)
    png_bytes = reveg_alg.plot.generate_chart(max_years=years)
    return Response(png_bytes.getvalue(), mimetype='image/png')


def root():
    return jsonify({
        '_links': [{
            'rel': 'pollination',
            'href': '/pollination'
        }, {
            'rel': 'tester-ui',
            'href': '/tester'
        }, {
            'rel': 'estimate',
            'href': '/estimate-runtime',
            'params': {
                'years': {
                    'type': 'integer'
                }
            }
        }, {
            'rel': 'reveg-curve',
            'href': '/reveg-curve.png',
            'params': {
                'years': {
                    'type': 'integer'
                }
            }
        }]
    })


def validate_request(request_dict, force_crop=False):
    try:
        required_keys = ['years', crop_type_key, 'farm', 'reveg']
        for curr in required_keys:
            request_dict[curr]
    except KeyError:
        raise InvalidUsage('POST body must have the keys: ' +
                           str(required_keys))
    valid_crop_types = ['apple', 'canola', 'lucerne']
    crop_type = request_dict[crop_type_key]
    if not crop_type in valid_crop_types:
        raise InvalidUsage('crop_type must be one of: ' +
                           str(valid_crop_types))
    assert_geojson(request_dict['farm'])
    assert_geojson(request_dict['reveg'])
    assert_json_schema()
    # FIXME validate socketio_sid


def assert_json_schema():
    class JsonInputs(Inputs):
        json = [JsonSchema(schema=pollination_schema)]

    inputs = JsonInputs(request)
    if inputs.validate():
        return
    logger.debug('validation errors=%s' % inputs.errors)
    raise InvalidUsage('JSON schema validation failed: ' + str(inputs.errors))


def assert_geojson(geojson_dict):
    try:
        geojson.loads(dumps(geojson_dict))
    except ValueError as e:
        raise InvalidUsage('Not valid geojson: ' + e.message)


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


class AppBuilder(object):
    def __init__(self, model_runner):
        self.model_runner = model_runner

    def set_socketio(self, socketio):
        self.socketio = socketio

    def build(self):
        app = Flask(__name__)
        self.app = app
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
        self._bind_routes()

        @app.errorhandler(InvalidUsage)
        def handle_invalid_usage(error):
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
            return response

        return app

    def _bind_routes(self):
        def post_route(rule, view_func):
            self.app.add_url_rule(rule,
                                  rule.replace('/', ''),
                                  view_func,
                                  methods=['POST'])

        self.app.add_url_rule('/', 'root', root)
        post_route('/pollination', self.pollination)
        self.app.add_url_rule('/tester', view_func=tester)
        self.app.add_url_rule('/get-sample-data',
                              view_func=self.get_sample_data)
        post_route('/run-sample', self.run_sample)
        self.app.add_url_rule('/estimate-runtime', view_func=estimate_runtime)
        self.app.add_url_rule('/reveg-curve.png', view_func=reveg_curve_png)


    def get_sample_data(self):
        """ gets data the UI needs to run the official NatCap sample data """
        self.model_runner.run_prep_sample_data_script()
        with open('/data/pollination-sample/ui.json') as f:
            content = f.read()
            resp = Response(content, mimetype='application/json')
            return resp

    @accept('application/json')
    def run_sample(self):
        """ executes the InVEST pollination model using the raster from the
        official NatCap sample data """
        runner_fn = self.model_runner.execute_model_for_sample_data
        return self.do_handle_request(runner_fn)

    @accept('application/json')
    def pollination(self):
        """ executes the InVEST pollination model and returns the results """
        runner_fn = self.model_runner.execute_model
        return self.do_handle_request(runner_fn)

    def do_handle_request(self, runner_fn):
        if not request.is_json:
            raise InvalidUsage("POST body doesn't look like JSON", 415)
        post_body = request.get_json()
        try:
            validate_request(post_body)
        except Exception as e:
            is_force = request.args.get('force', default=False, type=bool)
            if is_force:
                logger.exception('Error during validation but forcing onwards')
            else:
                raise e
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
        try:
            socketio_sid = post_body['socketio_sid']
        except KeyError:
            socketio_sid = None

        def mark_year_as_done():
            if not socketio_sid:
                return
            self.socketio.emit(
                'year-complete',
                {'msg': 'completed another year in the simulation'},
                room=socketio_sid)
            self.socketio.sleep(0)  # flush

        result = runner_fn(geojson_farm_vector,
                           years_to_simulate,
                           geojson_reveg_vector,
                           crop_type, mark_year_as_done)

        return jsonify(result)
