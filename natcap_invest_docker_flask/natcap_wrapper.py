import time
import csv
import os
import copy
import shutil
import logging
import base64
import multiprocessing as mp
import uuid

import natcap.invest.pollination
import shapefile
import subprocess32 as subprocess
import osgeo.ogr as ogr
import osgeo.osr as osr
import numpy as np
from flask.json import dumps

from natcap_invest_docker_flask.helpers import get_records
from reveg_alg.alg import get_values_for_year

KNOWN_LAYER_NAME = 'reveg_geojson'  # ogr2ogr will use the filename as the layer name

logger = logging.getLogger('natcap_wrapper')
pygeo_logger = logging.getLogger('pygeoprocessing.geoprocessing')
pygeo_logger.setLevel(logging.WARN)

metres_of_padding_for_farm = int(os.getenv('FARM_PADDING_METRES', 3000))
logger.info('Using farm padding of %d metres' % metres_of_padding_for_farm)
is_purge_workspace = bool(int(os.getenv('PURGE_WORKSPACE', 1)))
logger.info('Purge workspace after run = %s' % is_purge_workspace)

data_dir_path = u'/data/pollination'
app_docker_dir_path = u'/app/docker'
workspace_parent_dir_path = u'/workspace/'
reveg_lucode = 1337
farm_lucode = 2000  # TODO do we need to add this as an entry to the LULC table or is the farm ignored?
biophys_col_count = 5  # ignore LU_DESCRIP and comment
farm_layer_and_file_name = u'farms'
reproj_reveg_filename = u'reprojected_' + KNOWN_LAYER_NAME + '.json'
FAILURE_FLAG = 'BANG!!!'


def landcover_biophys_table_path(crop_type):
    return os.path.join(app_docker_dir_path, u'landcover_biophysical_table',
                        crop_type + u'.csv')


def farm_attribute_table_path(crop_type):
    return os.path.join(app_docker_dir_path, u'farm_attribute_table',
                        crop_type + u'.csv')


def workspace_path(suffix):
    return os.path.join(workspace_parent_dir_path, str(suffix))


def now_in_ms():
    return int(round(time.time() * 1000.0))


def generate_unique_token():
    return '%d_%s' % (now_in_ms(), uuid.uuid4())


def get_reveg_biophysical_table_row_for_year(year):
    val = get_values_for_year(year)
    return [[
        reveg_lucode,
        val['nesting_cavity'],
        val['nesting_ground'],
        val['fr_spring'],
        val['fr_summer'],
    ]]


def run_natcap_pollination(farm_vector_path, landcover_biophysical_table_path,
                           landcover_raster_path, workspace_dir_path,
                           crop_type):
    """ executes the pollination model and gathers the results """
    args = {
        u'farm_vector_path':
        farm_vector_path,
        u'guild_table_path':
        os.path.join(app_docker_dir_path, u'guild_table', crop_type + u'.csv'),
        u'landcover_biophysical_table_path':
        landcover_biophysical_table_path,
        u'landcover_raster_path':
        landcover_raster_path,
        u'results_suffix':
        u'',
        u'workspace_dir':
        workspace_dir_path,
    }
    natcap.invest.pollination.execute(args)
    farm_results = shapefile.Reader(
        os.path.join(workspace_dir_path, u'farm_results'))
    records = get_records(farm_results.records(), farm_results.fields)
    return records


def append_records(record_collector, new_records, year_number):
    for curr in new_records:
        curr.update({'year': year_number})
        record_collector.append(curr)


def fill_in_and_write(biophys_table, file_path):
    """
    Add default entries for all missing LULC codes and write to filesystem
      biophys_table:  2d numpy array of existing LULC records
      file_path:      where to write the CSV
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
    # TODO perhaps should read this header from the CSV file(s)
    with open(file_path, 'w') as f:
        f.write('lucode,')
        f.write('nesting_cavity_availability_index,')
        f.write('nesting_ground_availability_index,')
        f.write('floral_resources_spring_index,')
        f.write('floral_resources_summer_index\n')
        format_template = ','.join(['%d' for x in range(biophys_col_count)])
        np.savetxt(f, completed_table, fmt=format_template)


def read_biophys_table_from_file(file_path):
    return np.genfromtxt(file_path,
                         skip_header=1,
                         delimiter=',',
                         usecols=range(biophys_col_count))


def run_year0(farm_vector_path, landcover_raster_path, workspace_dir,
              output_queue, crop_type):
    try:
        logger.debug('processing year 0')
        year0_workspace_dir_path = os.path.join(workspace_dir, 'year0')
        os.mkdir(year0_workspace_dir_path)
        landcover_bp_table_path = landcover_biophys_table_path(crop_type)
        bp_table = read_biophys_table_from_file(landcover_bp_table_path)
        year0_biophys_table_path = os.path.join(
            year0_workspace_dir_path, 'landcover_biophysical_table.csv')
        fill_in_and_write(bp_table, year0_biophys_table_path)
        records = run_natcap_pollination(farm_vector_path,
                                         year0_biophys_table_path,
                                         landcover_raster_path,
                                         year0_workspace_dir_path, crop_type)
        output_queue.put((0, records))
    except Exception:
        logger.exception(
            'Failed while processing year 0')  # stack trace will be included
        output_queue.put(FAILURE_FLAG)


def run_future_year(farm_vector_path, landcover_raster_path, workspace_dir,
                    year_number, reveg_vector, output_queue, crop_type):
    try:
        logger.debug('processing year %s' % str(year_number))
        year_workspace_dir_path = os.path.join(workspace_dir,
                                               'year' + str(year_number))
        os.mkdir(year_workspace_dir_path)
        base_landcover_bp_table_path = landcover_biophys_table_path(crop_type)
        bp_table = np.genfromtxt(base_landcover_bp_table_path,
                                 skip_header=1,
                                 delimiter=',',
                                 usecols=range(biophys_col_count))
        reveg_row = get_reveg_biophysical_table_row_for_year(year_number)
        new_bp_table = np.concatenate((bp_table, reveg_row), axis=0)
        curr_year_landcover_bp_table_path = os.path.join(
            year_workspace_dir_path, 'landcover_biophysical_table.csv')
        fill_in_and_write(new_bp_table, curr_year_landcover_bp_table_path)
        new_landcover_raster_path = burn_reveg_on_raster(
            landcover_raster_path, reveg_vector, year_workspace_dir_path)
        records = run_natcap_pollination(farm_vector_path,
                                         curr_year_landcover_bp_table_path,
                                         new_landcover_raster_path,
                                         year_workspace_dir_path, crop_type)
        output_queue.put((year_number, records))
    except Exception:
        logger.exception('Failed while processing year %d' %
                         year_number)  # stack trace will be included
        output_queue.put(FAILURE_FLAG)


def burn_reveg_on_raster(year0_raster_path, reveg_vector,
                         year_workspace_dir_path):
    """ clones the raster and burns the reveg landuse code into the clone using the vector """
    data = None
    result_path = os.path.join(year_workspace_dir_path, 'landcover_raster.tif')
    with open(year0_raster_path, 'r') as f:
        data = f.read()
    with open(result_path, 'w') as f:
        f.write(data)
    reveg_vector_path = os.path.join(year_workspace_dir_path,
                                     KNOWN_LAYER_NAME + '.json')
    with open(reveg_vector_path, 'w') as f:
        f.write(dumps(reveg_vector))
    reprojected_reveg_vector_path = reproject_geojson_to_epsg3107(
        year_workspace_dir_path, reveg_vector_path)
    # feel the burn!
    subprocess.check_call([
        '/usr/bin/gdal_rasterize', '-burn',
        str(reveg_lucode), '-l', KNOWN_LAYER_NAME,
        reprojected_reveg_vector_path, result_path
    ],
                          stdout=subprocess.DEVNULL)
    return result_path


def reproject_geojson_to_epsg3107(workspace_dir_path, geojson_path):
    result_path = os.path.join(workspace_dir_path, reproj_reveg_filename)
    subprocess.check_call(
        [
            '/usr/bin/ogr2ogr',
            '-s_srs',
            'EPSG:4326',  # assuming the incoming geojson has no CRS so WGS84 is implied
            '-t_srs',
            'EPSG:3107',
            '-f',
            'GeoJSON',
            result_path,
            geojson_path
        ],
        stdout=subprocess.DEVNULL)
    return result_path


def generate_images(workspace_dir, landcover_raster_path, farm_vector_path):
    """ generates the images and reads in the bytes of each image """
    result = {}
    year0_farm_on_raster_path = os.path.join(workspace_dir,
                                             'landcover_and_farm.png')
    burn_vector_script_path = os.path.join(app_docker_dir_path,
                                           'burn-vector-to-raster-png.sh')
    subprocess.check_call([
        burn_vector_script_path, landcover_raster_path,
        year0_farm_on_raster_path, farm_vector_path, farm_layer_and_file_name,
        str(farm_lucode)
    ],
                          stdout=subprocess.DEVNULL)
    with open(year0_farm_on_raster_path, 'rb') as f1:
        result['base'] = base64.b64encode(f1.read())
    reveg_vector_path = os.path.join(workspace_dir, 'year1',
                                     reproj_reveg_filename)
    is_only_year0_run = not os.path.isfile(reveg_vector_path)
    if is_only_year0_run:
        return result
    reveg_and_farm_on_raster_path = os.path.join(
        workspace_dir, 'landcover_and_farm_and_reveg.png')
    subprocess.check_call([
        burn_vector_script_path,
        year0_farm_on_raster_path.replace('.png', '.tif'),
        reveg_and_farm_on_raster_path, reveg_vector_path, KNOWN_LAYER_NAME,
        str(reveg_lucode)
    ],
                          stdout=subprocess.DEVNULL)
    with open(reveg_and_farm_on_raster_path, 'rb') as f2:
        result['reveg'] = base64.b64encode(f2.read())
    return result


def create_cropped_raster(farm_vector_path, workspace_dir):
    vector_extent = get_extent(farm_vector_path)
    full_raster_path = os.path.join(data_dir_path,
                                    u'south_australia_landcover.tif.gz')
    cropped_raster_path = os.path.join(workspace_dir, 'landcover_cropped.tif')
    subprocess.check_call(
        [
            '/usr/bin/gdal_translate',
            '-projwin',  # probably specific to southern hemisphere and Australia's side of 0 degree longitude
            vector_extent['x_min'],
            vector_extent['y_max'],
            vector_extent['x_max'],
            vector_extent['y_min'],
            '-of',
            'GTiff',
            u'/vsigzip/' + full_raster_path,
            cropped_raster_path
        ],
        stdout=subprocess.DEVNULL)
    return cropped_raster_path


def get_extent(farm_vector_path):
    sa_lambert_epsg_code = 3107
    target = osr.SpatialReference()
    target.ImportFromEPSG(sa_lambert_epsg_code)
    vector_ds = ogr.Open(farm_vector_path)
    vector_layer = vector_ds.GetLayer()
    geometry_collection = ogr.Geometry(ogr.wkbGeometryCollection)
    for curr_feature in vector_layer:
        geometry = curr_feature.GetGeometryRef()
        geometry.TransformTo(target)
        geometry_collection.AddGeometry(geometry)
    x_min, x_max, y_min, y_max = geometry_collection.GetEnvelope()
    return {
        'x_min': str(x_min - metres_of_padding_for_farm),
        'y_min': str(y_min - metres_of_padding_for_farm),
        'y_max': str(y_max + metres_of_padding_for_farm),
        'x_max': str(x_max + metres_of_padding_for_farm),
    }


def load_farm_attributes(crop_type):
    """ Loads the attributes for specified crop to be used in the farm vector
        attribute table """
    with open(farm_attribute_table_path(crop_type), 'rb') as f:
        reader = csv.DictReader(f)
        return list(reader)


def transform_geojson_to_shapefile(geojson_vector_from_user, filename_fragment,
                                   workspace_dir, crop_type):
    """ Writes the supplied GeoJSON to a file, then transforms it
        to a shapefile and returns the path to that shapefile """
    shapefile_path = os.path.join(workspace_dir, filename_fragment + u'.shp')
    geojson_path = os.path.join(workspace_dir, filename_fragment + u'.json')
    attr_table_rows = load_farm_attributes(crop_type)
    baked_geojson_vector = {'type': 'FeatureCollection', 'features': []}
    for curr_attr_row in attr_table_rows:
        # merge all the features into a multipolygon so we get a single result
        # per season, otherwise we'd have to somehow merge separate results.
        multipolygon = {
            'type': 'Feature',
            'properties': curr_attr_row,
            'geometry': {
                'type':
                'MultiPolygon',
                'coordinates': [
                    x['geometry']['coordinates']
                    for x in geojson_vector_from_user['features']
                ]
            }
        }
        multipolygon['properties']['crop_type'] = crop_type
        baked_geojson_vector['features'].append(copy.deepcopy(multipolygon))
    with open(geojson_path, 'w') as f:
        f.write(dumps(baked_geojson_vector))
    subprocess.check_call(
        [
            '/usr/bin/ogr2ogr',
            '-s_srs',
            'EPSG:4326',  # assume input geojson has no CRS, WGS84 is implied
            '-t_srs',
            'EPSG:3107',
            '-f',
            'ESRI Shapefile',
            shapefile_path,
            geojson_path
        ],
        stdout=subprocess.DEVNULL)
    return shapefile_path


class NatcapModelRunner(object):
    def execute_model(self, geojson_farm_vector, years_to_simulate,
                      geojson_reveg_vector, crop_type):
        start_ms = now_in_ms()
        workspace_dir = workspace_path(generate_unique_token())
        logger.debug('using workspace dir "%s"' % workspace_dir)
        os.mkdir(workspace_dir)
        farm_vector_path = transform_geojson_to_shapefile(
            geojson_farm_vector, farm_layer_and_file_name, workspace_dir,
            crop_type)
        landcover_raster_path = create_cropped_raster(farm_vector_path,
                                                      workspace_dir)
        output = mp.Queue()
        processes = []
        processes.append(
            mp.Process(target=run_year0,
                       args=((farm_vector_path, landcover_raster_path,
                              workspace_dir, output, crop_type))))
        for curr_year in range(1, years_to_simulate + 1):
            processes.append(
                mp.Process(target=run_future_year,
                           args=((farm_vector_path, landcover_raster_path,
                                  workspace_dir, curr_year,
                                  geojson_reveg_vector, output, crop_type))))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        queue_results = []
        for p in processes:
            process_result = output.get()
            if process_result == FAILURE_FLAG:
                raise RuntimeError('Failed while executing the model')
            queue_results.append(process_result)
        queue_results.sort()
        records = []
        for curr in queue_results:
            year_num = curr[0]
            year_records = curr[1]
            append_records(records, year_records, year_num)
        result = {
            'images':
            generate_images(workspace_dir, landcover_raster_path,
                            farm_vector_path),
            'records':
            records,
            'elapsed_ms':
            now_in_ms() - start_ms
        }
        if is_purge_workspace:
            shutil.rmtree(workspace_dir)
        logger.debug('execution time %dms' % result['elapsed_ms'])
        return result
