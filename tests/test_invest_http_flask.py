import unittest
import os

from flask import abort
from flask.json import loads

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
            def execute_model(self):
                return {
                    'images': [
                        '/images/123/image1.png',
                        '/images/123/image2.png'
                    ],
                    'records': [{
                        'crop_type': 'apples',
                        'season': 'spring'
                    }, {
                        'crop_type': 'pears',
                        'season': 'summer'
                    }]
                }
        result = self.app(StubModelRunner()).get('/pollination')
        self.assertEqual(loads(result.data), {
            'images': [
                '/images/123/image1.png',
                '/images/123/image2.png'
            ],
            'records': [{
                'crop_type': 'apples',
                'season': 'spring'
            }, {
                'crop_type': 'pears',
                'season': 'summer'
            }]
        })


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
