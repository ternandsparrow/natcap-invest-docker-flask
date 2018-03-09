import unittest
import os

from flask import abort
from flask.json import loads, dumps

from .context import natcap_invest_docker_flask

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
        farm_vector_path = os.path.join(os.path.dirname(__file__), '../natcap_invest_docker_flask/static/example-farm-vector.json')
        with open(farm_vector_path) as f:
            data = f.read()
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
        """ Does a valid GeoJSON object that is missing the required properties on features fail validation? """
        farm_vector_path = os.path.join(os.path.dirname(__file__), '../natcap_invest_docker_flask/static/example-farm-vector.json')
        with open(farm_vector_path) as f:
            data = loads(f.read())
            for curr in data['features']:
                del curr['properties']
                curr['properties'] = []
            data = dumps(data)
        result = self.app().post('/pollination', data=data,
                content_type='application/json', headers={'accept': 'application/json'})
        self.assertEqual(result.status_code, 422)


    def test_get_png01(self):
        """ can we get a PNG when it is present? """
        parentself = self
        class StubModelRunner(object):
            def get_png(self, uniqueworkspace, imagename):
                parentself.assertEqual(uniqueworkspace, '456')
                parentself.assertEqual(imagename, 'someimage.png')
                thisdir = os.path.dirname(os.path.realpath(__file__))
                return os.path.join(thisdir, 'onewhitepixel.png')
        result = self.app(StubModelRunner()).get('/image/456/someimage.png')
        first8bytes = ':'.join(x.encode('hex') for x in result.data[0:8])
        png_magic_number = '89:50:4e:47:0d:0a:1a:0a'
        self.assertEqual(first8bytes, png_magic_number)


    def test_get_png02(self):
        """ is a non-200 status code propgated up? """
        class StubModelRunner(object):
            def get_png(self, uniqueworkspace, imagename):
                raise natcap_invest_docker_flask.SomethingFailedException(abort(404))
        result = self.app(StubModelRunner()).get('/image/456/notthere.png')
        self.assertEqual(result.status_code, 404)


    def test_tester01(self):
        """ can we get the tester UI? """
        result = self.app().get('/tester')
        self.assertEqual(result.data[0:33], '<!DOCTYPE html>\n<html lang="en">\n')
