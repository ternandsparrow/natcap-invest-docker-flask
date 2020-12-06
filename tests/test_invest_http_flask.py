import unittest
import os
import logging

from flask.json import loads, load, dumps

from .context import natcap_invest_docker_flask
from natcap_invest_docker_flask.invest_http_flask \
    import logger as object_under_test_logger

object_under_test_logger.setLevel(
    logging.INFO)  # we don't need our console flooded


class Test(unittest.TestCase):
    def init_test_app(self, model_runner=None):
        temp_app = natcap_invest_docker_flask.AppBuilder(model_runner).build()
        temp_app.testing = True
        return temp_app.test_client()

    def test_root01(self):
        """ can we GET the root? """
        result = self.init_test_app().get('/')
        self.assertEqual(
            loads(result.data), {
                '_links': [{
                    'rel': 'pollination',
                    'href': '/pollination'
                }, {
                    'rel': 'tester-ui',
                    'href': '/tester'
                }, {
                    'href': "/estimate-runtime",
                    'params': {
                        'years': {
                            'type': "integer"
                        }
                    },
                    'rel': "estimate"
                }, {
                    'href': "/reveg-curve.png",
                    'params': {
                        'years': {
                            'type': "integer"
                        }
                    },
                    'rel': "reveg-curve"
                }]
            })

    def test_pollination01(self):
        """ can we execute the pollination model? """
        class StubModelRunner(object):
            def execute_model(self, geojson_farm_vector, years_to_simulate,
                              geojson_reveg_vector, crop_type,
                              mark_year_as_done_fn, varroa_mite_year):
                return {
                    'images': ['/images/123/image1.png'],
                    'records': [{
                        'crop_type': 'pears',
                        'season': 'summer'
                    }]
                }

        static_files_dir_path = os.path.join(os.path.dirname(__file__), '..',
                                             'natcap_invest_docker_flask',
                                             'static')
        with open(
                os.path.join(static_files_dir_path,
                             'example-farm-vector.json')) as f:
            farm_data = load(f)
        with open(
                os.path.join(static_files_dir_path,
                             'example-reveg-vector.json')) as f:
            reveg_data = load(f)
        data = dumps({'crop_type': 'apple', 'years': 3,
                      'varroa_mite_year': 2, 'farm': farm_data,
                      'reveg': reveg_data})
        result = self.init_test_app(StubModelRunner()).post(
            '/pollination',
            data=data,
            content_type='application/json',
            headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(
            loads(result.data), {
                'images': ['/images/123/image1.png'],
                'records': [{
                    'crop_type': 'pears',
                    'season': 'summer'
                }]
            })

    def test_pollination02(self):
        """ Do we get a 406 when we accept something that isn't JSON """
        data = u'<foo>bar</foo>'
        not_json_mimetype = 'application/xml'
        result = self.init_test_app().post(
            '/pollination',
            data=data,
            content_type='application/json',
            headers={'accept': not_json_mimetype})
        self.assertEqual(result.status_code, 406)

    def test_pollination03(self):
        """ Do we get a 406 when we don't provide an accept header """
        data = u'{"foo":"bar"}'
        result = self.init_test_app().post('/pollination',
                                           data=data,
                                           content_type='application/json')
        self.assertEqual(result.status_code, 406)

    def test_pollination04(self):
        """ Do we get the expected 4xx response when we provide post POST body
        that doesn't validate """
        data = u'{"type":100}'
        result = self.init_test_app().post(
            '/pollination',
            data=data,
            content_type='application/json',
            headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 400)

    def test_pollination05(self):
        """ Do we get the expected 4xx response when we provide Content-type !=
        application/json """
        data = u'<blah>Not json</blah>'
        result = self.init_test_app().post(
            '/pollination',
            data=data,
            content_type='application/xml',
            headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 415)

    def test_pollination06(self):
        """ Do we get the expected 4xx response when we don't provide a body
        """
        result = self.init_test_app().post(
            '/pollination',
            content_type='application/json',
            headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 400)

    def test_pollination07(self):
        """ Does a valid farm GeoJSON object that is missing the required
        properties on features fail validation? """
        farm_vector_path = os.path.join(os.path.dirname(__file__), '..',
                                        'natcap_invest_docker_flask', 'static',
                                        'example-farm-vector.json')
        with open(farm_vector_path) as f:
            farm_data = loads(f.read())
            for curr in farm_data['features']:
                del curr['properties']
                curr['properties'] = []
            data = dumps({'farm': farm_data})
        result = self.init_test_app().post(
            '/pollination',
            data=data,
            content_type='application/json',
            headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 400)

    def test_pollination08(self):
        """ Do we get the expected 4xx response when we provide post POST body
        that has a farm field but doesn't validate """
        data = u'{"farm": {"type":100} }'
        result = self.init_test_app().post(
            '/pollination',
            data=data,
            content_type='application/json',
            headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 400)

    def test_pollination09(self):
        """ Do we get the expected 4xx response when we supply a 'year' param
        that's too large """
        data = u'{"years":55,"crop_type":"canola","reveg":{},"farm":{}}'

        class Stub:
            def execute_model_for_sample_data(self):
                raise Exception('should not be called')

        orig_level = object_under_test_logger.level
        object_under_test_logger.setLevel(logging.FATAL)
        result = self.init_test_app(Stub()).post(
            # using this instead of /pollination so we don't have to craft
            # valid geojson vectors in the req body.
            '/run-sample',
            data=data,
            content_type='application/json',
            headers={'accept': 'application/json'})
        object_under_test_logger.setLevel(orig_level)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.content_type, 'application/json')
        self.assertEqual(
            loads(result.data),
            {'message': 'years cannot be > 30'})

    def test_tester01(self):
        """ can we get the tester UI? """
        result = self.init_test_app().get('/tester')
        self.assertEqual(result.data[0:33],
                         b'<!DOCTYPE html>\n<html lang="en">\n')
