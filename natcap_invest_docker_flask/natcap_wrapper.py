import time
import math
import csv
import os
import copy
import shutil
import logging
import base64
# Note for eventlet: DO NOT call eventlet.monkey_patch(), it doesn't
# work with multiprocessing
import multiprocessing as mp
import uuid

import natcap.invest.pollination
import shapefile
import subprocess32 as subprocess
import osgeo.ogr as ogr
import osgeo.osr as osr
import numpy as np
from flask.json import dumps

from natcap_invest_docker_flask.helpers import \
    get_records, biophys_col_count, fill_in_and_write, \
    subtract_reveg_from_farm, append_to_2d_np
from natcap_invest_docker_flask.logger import logger_getter
from reveg_alg.alg import get_values_for_year

# ogr2ogr defaults to the filename as the layer name, we want something more
# predictable
KNOWN_REVEG_LAYER_NAME = 'reveg_geojson'

logger = logger_getter.get_app_logger()
logging.getLogger('natcap').setLevel(logging.WARN)
logging.getLogger('taskgraph').setLevel(logging.WARN)
logging.getLogger('pygeoprocessing').setLevel(logging.WARN)

metres_of_padding_for_farm = int(os.getenv('FARM_PADDING_METRES', 1500))
logger.info(f'Using farm padding of {metres_of_padding_for_farm} metres')
is_purge_workspace = bool(int(os.getenv('PURGE_WORKSPACE', 1)))
logger.info(f'Purge workspace after run = {is_purge_workspace}')
is_farm_vector_chomped_for_year0 = bool(
    int(os.getenv('IS_CHOMP_FARM_VECTOR', 1)))
logger.info('Is chomping reveg out of farm vector for ' +
            f'year0? {is_farm_vector_chomped_for_year0}')

data_dir_path = u'/data/pollination'
app_docker_dir_path = u'/app/docker'
workspace_parent_dir_path = u'/workspace/'
reveg_lucode = 1337
farm_lucode = 2000  # only used for generating raster for humans
farm_layer_and_file_name = u'farms'
reproj_reveg_filename = u'reprojected_' + KNOWN_REVEG_LAYER_NAME + '.json'
FAILURE_FLAG = 'BANG!!!'


def subset_of_years(target_years):
    """ we don't need to run every year, so we can save compute by only running
    a nicely spread out subset """
    result = list(range(1, target_years + 1, math.ceil(target_years / 5)))
    if target_years not in result:
        result.append(target_years)
    return result


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


def get_reveg_biophysical_table_row_for_year(year, existing_bp_table):
    val = get_values_for_year(year)
    prefix = 'fr_'
    fr_cols = filter(lambda x: x.startswith(prefix), val.keys())
    for curr in list(fr_cols):
        season = curr.replace(prefix, '')
        try:
            key = f'floral_resources_{season}_index'
            existing_bp_table[key]
            fr_season_col_val = val[curr]
            # continue so we delete the other values
        except ValueError:
            # purely so we can have nice, named debug output
            del val[curr]
            continue
    if not fr_season_col_val:
        raise ValueError('Programmer error: could not find a ' +
                         f'{prefix} col value')
    logger.debug(f'[year {year}] biophys table reveg row is {val}')
    return [
        reveg_lucode,
        val['nesting_cavity'],
        val['nesting_ground'],
        fr_season_col_val,
    ]


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


def read_biophys_table_from_file(file_path):
    return np.genfromtxt(file_path,
                         delimiter=',',
                         names=True,
                         usecols=range(biophys_col_count))


def debug_dump_bp_table(bp_table, year_num):
    if not logger.isEnabledFor(logging.DEBUG):
        return
    # thanks https://stackoverflow.com/a/2891805/1410035
    with np.printoptions(precision=5, suppress=True):
        header = bp_table.dtype.names
        logger.debug(f'[year {year_num}] biophys table:\n{header}\n{bp_table}')


def run_year0(farm_vector_path, landcover_raster_path, workspace_dir,
              output_queue, crop_type):
    try:
        logger.debug('processing year 0')
        year0_workspace_dir_path = os.path.join(workspace_dir, 'year0')
        os.mkdir(year0_workspace_dir_path)
        landcover_bp_table_path = landcover_biophys_table_path(crop_type)
        bp_table = read_biophys_table_from_file(landcover_bp_table_path)
        debug_dump_bp_table(bp_table, 0)
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
        bp_table = build_biophys_table(crop_type, year_number)
        debug_dump_bp_table(bp_table, year_number)
        curr_year_landcover_bp_table_path = os.path.join(
            year_workspace_dir_path, 'landcover_biophysical_table.csv')
        fill_in_and_write(bp_table, curr_year_landcover_bp_table_path)
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


def build_biophys_table(crop_type, year_number):
    base_landcover_bp_table_path = landcover_biophys_table_path(crop_type)
    bp_table = read_biophys_table_from_file(base_landcover_bp_table_path)
    reveg_row = get_reveg_biophysical_table_row_for_year(year_number, bp_table)
    return append_to_2d_np(bp_table, reveg_row)


def burn_reveg_on_raster(year0_raster_path, reveg_vector,
                         year_workspace_dir_path):
    """ clones the raster and burns the reveg landuse code into the clone using
    the vector """
    data = None
    result_path = os.path.join(year_workspace_dir_path, 'landcover_raster.tif')
    with open(year0_raster_path, 'rb') as f:
        data = f.read()
    with open(result_path, 'wb') as f:
        f.write(data)
    reprojected_reveg_vector_path = reproject_geojson_to_epsg3107(
        year_workspace_dir_path, reveg_vector)
    # feel the burn!
    subprocess.check_call([
        '/usr/bin/gdal_rasterize', '-burn',
        str(reveg_lucode), '-l', KNOWN_REVEG_LAYER_NAME,
        reprojected_reveg_vector_path, result_path
    ],
        stdout=subprocess.DEVNULL)
    return result_path


def reproject_geojson_to_epsg3107(workspace_dir_path, reveg_geojson):
    reveg_vector_path = os.path.join(workspace_dir_path,
                                     KNOWN_REVEG_LAYER_NAME + '.json')
    with open(reveg_vector_path, 'w') as f:
        f.write(dumps(reveg_geojson))
    result_path = os.path.join(workspace_dir_path, reproj_reveg_filename)
    crs = get_crs_from_geojson(reveg_geojson)
    subprocess.check_call([
        '/usr/bin/ogr2ogr', '-s_srs', crs, '-t_srs', 'EPSG:3107', '-f',
        'GeoJSON', result_path, reveg_vector_path
    ],
        stdout=subprocess.DEVNULL)
    return result_path


def generate_images(workspace_dir, landcover_raster_path, farm_vector_path):
    """ generates the images and reads in the bytes of each image """
    result = {}
    farm_on_raster_path = os.path.join(workspace_dir,
                                       'landcover_and_farm.png')
    burn_vector_script_path = os.path.join(app_docker_dir_path,
                                           'burn-vector-to-raster-png.sh')
    subprocess.check_call([
        burn_vector_script_path, landcover_raster_path,
        farm_on_raster_path, farm_vector_path, farm_layer_and_file_name,
        str(farm_lucode)
    ],
        stdout=subprocess.DEVNULL)
    with open(farm_on_raster_path, 'rb') as f1:
        result['base'] = base64.b64encode(f1.read()).decode('utf-8')
    reveg_vector_path = os.path.join(workspace_dir, 'year1',
                                     reproj_reveg_filename)
    is_only_year0_run = not os.path.isfile(reveg_vector_path)
    if is_only_year0_run:
        return result
    reveg_and_farm_on_raster_path = os.path.join(
        workspace_dir, 'landcover_and_farm_and_reveg.png')
    subprocess.check_call([
        burn_vector_script_path,
        farm_on_raster_path.replace('.png', '.tif'),
        reveg_and_farm_on_raster_path, reveg_vector_path, KNOWN_REVEG_LAYER_NAME,
        str(reveg_lucode)
    ],
        stdout=subprocess.DEVNULL)
    with open(reveg_and_farm_on_raster_path, 'rb') as f2:
        result['reveg'] = base64.b64encode(f2.read()).decode('utf-8')
    return result


def create_cropped_raster(farm_vector_path, workspace_dir):
    vector_extent = get_extent(farm_vector_path)
    full_raster_path = os.path.join(data_dir_path,
                                    u'south_australia_landcover.tif.gz')
    cropped_raster_path = os.path.join(workspace_dir, 'landcover_cropped.tif')
    subprocess.check_call(
        [
            '/usr/bin/gdal_translate',
            '-projwin',
            # probably specific to southern hemisphere and Australia's side of
            # 0 degree longitude.
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
    with open(farm_attribute_table_path(crop_type), 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def transform_geojson_to_shapefile(geojson_vector_from_user, filename_fragment,
                                   workspace_dir, crop_type):
    """ Writes the supplied GeoJSON to a file, then transforms it
        to a shapefile and returns the path to that shapefile """
    shapefile_path = os.path.join(workspace_dir, filename_fragment + u'.shp')
    geojson_path = os.path.join(workspace_dir, filename_fragment + u'.json')
    attr_table_rows = load_farm_attributes(crop_type)
    if len(attr_table_rows) < 1:
        logger.warn('No farm attribute rows found for crop %s' % crop_type)
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
                    # note: we don't support MultiPolygons from the user. We
                    # could but our use case doesn't require it.
                    x['geometry']['coordinates']
                    for x in geojson_vector_from_user['features']
                ]
            }
        }
        multipolygon['properties']['crop_type'] = crop_type
        baked_geojson_vector['features'].append(copy.deepcopy(multipolygon))
    crs = get_crs_from_geojson(geojson_vector_from_user)
    with open(geojson_path, 'w') as f:
        f.write(dumps(baked_geojson_vector))
    subprocess.check_call([
        '/usr/bin/ogr2ogr', '-s_srs', crs, '-t_srs', 'EPSG:3107', '-f',
        'ESRI Shapefile', shapefile_path, geojson_path
    ],
        stdout=subprocess.DEVNULL)
    return shapefile_path


def get_crs_from_geojson(the_geojson):
    try:
        result = the_geojson['crs']['properties']['name']
        logger.debug('Using CRS from user input: %s' % result)
        return result
    except KeyError:
        return 'EPSG:4326'


class NatcapModelRunner(object):
    def execute_model(self, *args, **kwargs):
        return self._execute_model(create_cropped_raster, *args, **kwargs)

    def execute_model_for_sample_data(self, *args, **kwargs):
        def raster_fn(_, _2):
            # only works in the docker container, because the data comes from
            # the base image.
            return u'/data/pollination-sample/landcover.tif'

        return self._execute_model(raster_fn, *args, **kwargs)

    def _execute_model(self, landcover_raster_cropper_fn, geojson_farm_vector,
                       years_to_simulate, geojson_reveg_vector, crop_type,
                       mark_year_as_done_fn):
        start_ms = now_in_ms()
        workspace_dir = workspace_path(generate_unique_token())
        logger.debug(f'using workspace dir "{workspace_dir}"')
        os.mkdir(workspace_dir)
        farm_vector_minus_reveg_geojson = subtract_reveg_from_farm(
            geojson_farm_vector, geojson_reveg_vector)
        farm_vector_minus_reveg_path = transform_geojson_to_shapefile(
            farm_vector_minus_reveg_geojson,
            farm_layer_and_file_name, workspace_dir,
            crop_type)
        # year 0 can use either farm vector, but future years *must* use the
        # chomped vector.
        if is_farm_vector_chomped_for_year0:
            logger.debug('Year 0 using *chomped* farm vector')
            farm_vector_path = farm_vector_minus_reveg_path
        else:
            logger.debug('Year 0 using original (non-chomped) farm vector')
            farm_vector_path = transform_geojson_to_shapefile(
                geojson_farm_vector, farm_layer_and_file_name, workspace_dir,
                crop_type)
        landcover_raster_path = landcover_raster_cropper_fn(
            farm_vector_path, workspace_dir)

        # we use a pool so we can limit the number of concurrent processes. If
        # we just create processes we would either need to manage what's
        # running ourselves or have them all run at the same time
        pool = mp.Pool(mp.cpu_count())
        # TODO ideally we'd have one Pool that is used by all clients, not one
        # pool per HTTP request
        manager = mp.Manager()
        output = manager.Queue()
        processes = []

        processes.append(
            pool.apply_async(run_year0,
                             (farm_vector_path, landcover_raster_path,
                              workspace_dir, output, crop_type)))
        for curr_year in subset_of_years(years_to_simulate):
            processes.append(
                pool.apply_async(
                    run_future_year,
                    (farm_vector_minus_reveg_path, landcover_raster_path,
                     workspace_dir, curr_year, geojson_reveg_vector, output,
                     crop_type)))
        queue_results = []
        pool.close()
        # we don't pool.join(), instead we block on the results in the queue so
        # we can fire notifications as processes finish. We trust that once we
        # have all the results, all the processes are finished.
        for p in processes:
            process_result = output.get()
            if process_result == FAILURE_FLAG:
                raise RuntimeError('Failed while executing the model')
            mark_year_as_done_fn()
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
