import unittest
import os
import logging

from flask import abort
from flask.json import loads, dumps

from .context import natcap_invest_docker_flask
from natcap_invest_docker_flask.invest_http_flask import logger as object_under_test_logger

object_under_test_logger.setLevel(logging.INFO) # we don't need our console flooded

class Test(unittest.TestCase):
    def app(self, model_runner=None):
        temp_app = natcap_invest_docker_flask.make_app(model_runner)
        temp_app.testing = True
        return temp_app.test_client()


    def test_root01(self):
        """ can we GET the root? """
        result = self.app().get('/')
        self.assertEqual(loads(result.data), {
            '_links': [
                {'rel': 'pollination', 'href': '/pollination'},
                {'rel': 'tester-ui', 'href': '/tester'}
            ]
        })


    def test_pollination01(self):
        """ can we execute the pollination model? """
        class StubModelRunner(object):
            def execute_model(self, geojson_farm_vector, years_to_simulate, geojson_reveg_vector):
                return {
                    'images': ['/images/123/image1.png'],
                    'records': [{
                        'crop_type': 'pears',
                        'season': 'summer'
                    }]
                }
        static_files_dir_path = os.path.join(os.path.dirname(__file__), '..', 'natcap_invest_docker_flask', 'static')
        with open(os.path.join(static_files_dir_path, 'example-farm-vector.json')) as f:
            farm_data = f.read()
        with open(os.path.join(static_files_dir_path, 'example-reveg-vector.json')) as f:
            reveg_data = f.read()
        data = '{"farm":%s,"reveg":%s}' % (farm_data, reveg_data)
        result = self.app(StubModelRunner()).post('/pollination', data=data,
                content_type='application/json', headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(loads(result.data), {
            'images': ['/images/123/image1.png'],
            'records': [{
                'crop_type': 'pears',
                'season': 'summer'
            }]
        })

    def test_pollination02(self):
        """ Do we get a 406 when we accept something that isn't JSON """
        data = u'{"foo":"bar"}'
        not_json_mimetype = 'application/xml'
        result = self.app().post('/pollination', data=data,
                content_type='application/json', headers={'accept': not_json_mimetype})
        self.assertEqual(result.status_code, 406)


    def test_pollination03(self):
        """ Do we get a 406 when we don't provide an accept header """
        data = u'{"foo":"bar"}'
        result = self.app().post('/pollination', data=data,
                content_type='application/json')
        self.assertEqual(result.status_code, 406)


    def test_pollination04 (self):
        """ Do we get the expected 4xx response when we provide post POST body that doesn't validate """
        data = u'{"type":100}'
        result = self.app().post('/pollination', data=data,
                content_type='application/json', headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 422)


    def test_pollination05 (self):
        """ Do we get the expected 4xx response when we provide Content-type != application/json """
        data = u'<blah>Not json</blah>'
        result = self.app().post('/pollination', data=data,
                content_type='application/xml', headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 415)


    def test_pollination06 (self):
        """ Do we get the expected 4xx response when we don't provide a body """
        result = self.app().post('/pollination',
                content_type='application/json', headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 400)


    def test_pollination07(self):
        """ Does a valid farm GeoJSON object that is missing the required properties on features fail validation? """
        farm_vector_path = os.path.join(os.path.dirname(__file__), '..', 'natcap_invest_docker_flask', 'static', 'example-farm-vector.json')
        with open(farm_vector_path) as f:
            farm_data = loads(f.read())
            for curr in farm_data['features']:
                del curr['properties']
                curr['properties'] = []
            data = dumps({'farm': farm_data})
        result = self.app().post('/pollination', data=data,
                content_type='application/json', headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 422)


    def test_pollination08 (self):
        """ Do we get the expected 4xx response when we provide post POST body that has a farm field but doesn't validate """
        data = u'{"farm": {"type":100} }'
        result = self.app().post('/pollination', data=data,
                content_type='application/json', headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 422)


    def test_pollination09 (self):
        """ Do we get the expected 4xx response when we supply a 'year' param that's too large """
        data = u'{ }'
        result = self.app().post('/pollination?years=300', data=data,
                content_type='application/json', headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.content_type, 'application/json')
        self.assertEqual(loads(result.data), {'message' : 'years param cannot be any larger than 30'})


    def test_tester01(self):
        """ can we get the tester UI? """
        result = self.app().get('/tester')
        self.assertEqual(result.data[0:33], '<!DOCTYPE html>\n<html lang="en">\n')
