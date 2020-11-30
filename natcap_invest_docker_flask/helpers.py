""" Stuff that is easier to unit test without all the other dependencies """
import numpy as np
from shapely.geometry import mapping, shape

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


def biophys_table_parent_of(v):
    """
    The SA biophysical landuse table codes are hierarchical. As an example: 111
    has a parent of 110. This function will take a code and tell you its parent
    code. There are only two levels, so parents are their own parents.
    """
    return v - (v % 10)


def fill_in_missing_lulc_rows(biophys_table):
    """
    Makes sure every LULC code has a row.
    Only some LULC codes have pollination value. Rather than storing all the
    rest as 0s, we generate those rows on the fly. Child rows that don't have
    an explicit value will inherit from their parent.
    """
    existing_lulc_codes = biophys_table[:, 0]
    extra_codes = []
    max_lulc_code = 699
    for curr in range(max_lulc_code):
        if curr in existing_lulc_codes:
            continue
        try:
            parent_code = biophys_table_parent_of(curr)
            parent_row = [x for x in biophys_table if x[0] == parent_code][0]
            # inherit parent values
            values = parent_row.copy()[1:]
        except IndexError:
            # no parent row, make it all 0s
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
        'lucode', 'nesting_cavity_availability_index',
        'nesting_ground_availability_index', 'floral_resources_spring_index',
        'floral_resources_summer_index'
    ])
    format_template = ','.join(['%g' for x in range(biophys_col_count)])
    np.savetxt(file_path,
               completed_table,
               fmt=format_template,
               header=header,
               comments='')


def feature_collection_to_multipolygon(f_coll):
    # shapely can't deal with Feature{Collection}s. At least with our tooling
    # and for our use case, I think a FeatureCollection *is* basically a
    # MultiPolygon, and shapely *does* handle them :D
    coords = []
    for curr_feat in f_coll['features']:
        the_type = curr_feat['geometry']['type']
        if the_type != 'Polygon':
            raise ValueError(
                f'Cannot handle {the_type}, only Polygon supported')
        coords.append(curr_feat['geometry']['coordinates'])
    return {'type': 'MultiPolygon', 'coordinates': coords}


def subtract_reveg_from_farm(farm_geojson, reveg_geojson):
    # doing this means the farm with reveg has a different area than the
    # original. It *needs* to be done though otherwise the farm shadows
    # the reveg on the raster and the reveg has 0 effect. It's probably not
    # safe to compare the result of two farms with different vectors.
    farm_shape = shape(feature_collection_to_multipolygon(farm_geojson))
    reveg_shape = shape(feature_collection_to_multipolygon(reveg_geojson))
    diffd = farm_shape.difference(reveg_shape)
    diffd_geojson = mapping(diffd)
    result = {
        "type":
        "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": diffd_geojson
        }]
    }
    return result
