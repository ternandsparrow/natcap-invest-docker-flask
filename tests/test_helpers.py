import unittest
from io import StringIO
import numpy as np
from .context import natcap_invest_docker_flask

objectundertest = natcap_invest_docker_flask


class Test(unittest.TestCase):
    def test_map_fields01(self):
        """ can we handle a basic record with two fields """
        record = ['almonds', 0.6]
        fields = [['crop_type', 'C', 80, 0], ['half_sat', 'N', 24, 15]]
        result = objectundertest.map_fields(record, fields)
        self.assertEqual(result, {'crop_type': 'almonds', 'half_sat': 0.6})

    def test_get_records01(self):
        """ can we map two records """
        records = [['almonds', 0.6], ['blueberries', 0.8]]
        fields = [('DeletionFlag', 'C', 1, 0), ['crop_type', 'C', 80, 0],
                  ['half_sat', 'N', 24, 15]]
        result = objectundertest.get_records(records, fields)
        self.assertEqual(result, [{
            'crop_type': 'almonds',
            'half_sat': 0.6
        }, {
            'crop_type': 'blueberries',
            'half_sat': 0.8
        }])

    def test_fill_in_missing_lulc_rows01(self):
        """ can we add in all the missing LULC code rows """
        bp_table = np.array([
            [110, 0.9, 0.7, 1.0, 0.4],
            [130, 0.6, 0.5, 0.5, 0.3],
            [210, 0.7, 0.1, 0.1, 0.2],
            [1337, 0.1, 0.7, 0.0, 0.0],
        ])
        result = objectundertest.fill_in_missing_lulc_rows(bp_table)
        reveg_row = 1
        self.assertEqual(len(result), 699 + reveg_row)
        # make sure explicit rows are untouched
        for curr_row_index in range(len(bp_table)):
            curr_row = bp_table[curr_row_index]
            for curr_col_index in range(len(curr_row)):
                curr_col = curr_row[curr_col_index]
                self.assertEqual(
                    result[curr_row_index][curr_col_index],
                    curr_col,
                    'row=%d, col=%d, val=%s is not equal'
                    % (curr_row_index, curr_col_index, curr_col))
        # make sure generated rows are as expected
        for curr_row_index in range(len(bp_table), len(result)):
            curr_row = result[curr_row_index]
            code = curr_row[0]
            self.assertGreaterEqual(code, 0)
            for curr_col_index in range(1, len(curr_row)):
                col_val = curr_row[curr_col_index]
                try:
                    parent_code = objectundertest.helpers.biophys_table_parent_of(
                        code)
                    parent_row = [
                        x for x in bp_table if x[0] == parent_code][0]
                    # should match the values for the parent
                    self.assertEqual(col_val, parent_row[curr_col_index])
                except IndexError:
                    # no parent row, should be all 0s
                    self.assertEqual(col_val, 0)

    def test_biophys_table_parent_of01(self):
        """ can we find the parent of a child """
        result = objectundertest.helpers.biophys_table_parent_of(111)
        self.assertEqual(result, 110)

    def test_biophys_table_parent_of02(self):
        """ is a parent its own parent? """
        result = objectundertest.helpers.biophys_table_parent_of(110)
        self.assertEqual(result, 110)

    def test_biophys_table_parent_of03(self):
        """ can we handle a value < 100 """
        result = objectundertest.helpers.biophys_table_parent_of(93)
        self.assertEqual(result, 90)

    def test_biophys_table_parent_of04(self):
        """ can we handle a value < 10 """
        result = objectundertest.helpers.biophys_table_parent_of(9)
        self.assertEqual(result, 0)

    def test_biophys_table_parent_of05(self):
        """ can we handle 0 """
        result = objectundertest.helpers.biophys_table_parent_of(0)
        self.assertEqual(result, 0)

    def test_fill_in_and_write01(self):
        """ can we write the biophys table CSV """
        bp_table = np.array([
            [110, 0.9, 0.7, 1.0, 0.4],
            [130, 0.6, 0.5, 0.5, 0.3],
            [210, 0.7, 0.1, 0.1, 0.2],
            [1337, 0.1, 0.7, 0.0, 0.0],
        ])
        outfile = StringIO()
        objectundertest.fill_in_and_write(bp_table, outfile)
        outfile.seek(0)
        result = outfile.read()
        expected = \
            'lucode,nesting_cavity_availability_index,nesting_ground_availability_index,floral_resources_spring_index,floral_resources_summer_index\n' + \
            '110,0.9,0.7,1,0.4\n' + \
            '130,0.6,0.5,0.5,0.3\n' + \
            '210,0.7,0.1,0.1,0.2\n' + \
            '1337,0.1,0.7,0,0\n' + \
            '0,0,0,0,0\n'
        self.assertEqual(result[:len(expected)], expected)
