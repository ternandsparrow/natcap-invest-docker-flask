import unittest

import geojson

class Test(unittest.TestCase):
    def test_loads01(self):
        """ is a JSON object with an understood type considered valid? """
        object_under_test = geojson.loads(u'{"type":"Feature"}')
        self.assertTrue(object_under_test.is_valid)


    def test_loads02(self):
        """ does a JSON object with an unknown type not really return a GeoJSON object?
            this is highlight behaviour I don't think is correct, we should always get .is_valid"""
        object_under_test = geojson.loads(u'{"type":"blah"}')
        self.assertFalse(hasattr(object_under_test, 'is_valid'))
