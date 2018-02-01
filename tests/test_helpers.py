import unittest
from .context import natcap_invest_docker_flask

objectundertest = natcap_invest_docker_flask.helpers

class Test(unittest.TestCase):
    def test_map_fields01(self):
        """ can we handle a basic record with two fields """
        record = ['almonds', 0.6]
        fields = [['crop_type', 'C', 80, 0], ['half_sat', 'N', 24, 15]]
        result = objectundertest.map_fields(record, fields)
        self.assertEqual(result, {
            'crop_type': 'almonds',
            'half_sat': 0.6
        })

    def test_get_records(self):
        """ can we map two records """
        records = [['almonds', 0.6], ['blueberries', 0.8]]
        fields = [('DeletionFlag', 'C', 1, 0), ['crop_type', 'C', 80, 0], ['half_sat', 'N', 24, 15]]
        result = objectundertest.get_records(records, fields)
        self.assertEqual(result, [
            {
                'crop_type': 'almonds',
                'half_sat': 0.6
            },
            {
                'crop_type': 'blueberries',
                'half_sat': 0.8
            }
        ])
