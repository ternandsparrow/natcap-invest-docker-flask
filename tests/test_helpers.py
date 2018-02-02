import unittest
from .context import natcap_invest_docker_flask

objectundertest = natcap_invest_docker_flask

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


    def test_get_records01(self):
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

    def test_extract_min_max01(self):
        """ can we extract the values when min==0 """
        src = '  Min=0 Max=0.37 \n'
        result = objectundertest.extract_min_max(src)
        self.assertEqual(result['min'], '0')
        self.assertEqual(result['max'], '0.37')

    def test_extract_min_max02(self):
        """ can we extract the values when min>0 """
        src = '  Min=0.073 Max=0.158 \n'
        result = objectundertest.extract_min_max(src)
        self.assertEqual(result['min'], '0.073')
        self.assertEqual(result['max'], '0.158')

    def test_extract_min_max03(self):
        """ is the expected error raised when a value can't be found """
        src = '  Min=0.073 \n'
        try:
            objectundertest.extract_min_max(src)
            self.fail()
        except AttributeError:
            # success!
            pass
