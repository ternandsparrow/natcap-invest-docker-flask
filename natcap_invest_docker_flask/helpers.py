""" Stuff that is easier to unit test without all the other dependencies """
import numpy as np

biophys_col_count = 5  # ignore LU_DESCRIP and comment cols


def get_records(records, all_fields):
    """ builds an array of record dicts """
    result = []
    fields = all_fields[1:]  # burn the 'DeletionFlag' field
    for curr in records:
        result.append(map_fields(curr, fields))
    return result


def map_fields(record, fields):
    """ creates a dict of field name => value for the supplied record """
    result = {}
    pos = 0
    for curr in fields:
        field_name = curr[0]
        value = record[pos]
        result[field_name] = value
        pos += 1
    return result


def fill_in_missing_lulc_rows(biophys_table):
    """
    Makes sure every LULC code has a row.
    Only some LULC codes have pollination value. Rather than storing all the
    rest as 0s, we generate those rows on the fly.
    """
    existing_lulc_codes = biophys_table[:, 0]
    extra_codes = []
    max_lulc_code = 699
    for curr in range(max_lulc_code):
        if curr in existing_lulc_codes:
            continue
        values = [0 for x in range(1, biophys_col_count)]
        extra_codes.append([curr] + list(values))
    completed_table = np.concatenate((biophys_table, extra_codes), axis=0)
    return completed_table


def fill_in_and_write(biophys_table, file_path):
    """
    Add default entries for all missing LULC codes and write to filesystem
      biophys_table:  2d numpy array of existing LULC records
      file_path:      where to write the CSV
    """
    completed_table = fill_in_missing_lulc_rows(biophys_table)
    # TODO perhaps should read this header from the CSV file(s)
    header = ','.join([
        'lucode',
        'nesting_cavity_availability_index',
        'nesting_ground_availability_index',
        'floral_resources_spring_index',
        'floral_resources_summer_index'
    ])
    format_template = ','.join(['%g' for x in range(biophys_col_count)])
    np.savetxt(file_path, completed_table, fmt=format_template,
               header=header, comments='')
