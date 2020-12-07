import time
import csv
import os
from copy import deepcopy
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
    subtract_reveg_from_farm, append_to_2d_np, subset_of_years
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

data_dir_path = u'/data/pollination'
app_docker_dir_path = u'/app/docker'
workspace_parent_dir_path = u'/workspace/'
reveg_lucode = 1337
farm_lucode = 2000  # only used for generating raster for humans
farm_layer_and_file_name = u'farms'
reproj_reveg_filename = u'reprojected_' + KNOWN_REVEG_LAYER_NAME + '.json'
FAILURE_FLAG = 'BANG!!!'
year_key = 'year'


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


def run_subprocess(args):
    subprocess.check_call(args, stdout=subprocess.DEVNULL)


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
                           crop_type, has_varroa_mite_hit):
    """ executes the pollination model and gathers the results """
    varroa_fragment = '_varroa' if has_varroa_mite_hit else ''
    guild_csv = f'{crop_type}{varroa_fragment}.csv'
    args = {
        u'farm_vector_path':
        farm_vector_path,
        u'guild_table_path':
        os.path.join(app_docker_dir_path, u'guild_table', guild_csv),
        u'landcover_biophysical_table_path':
        landcover_biophysical_table_path,
        u'landcover_raster_path':
        landcover_raster_path,
        u'results_suffix':
        varroa_fragment,
        u'workspace_dir':
        workspace_dir_path,
    }
    natcap.invest.pollination.execute(args)
    farm_results = shapefile.Reader(
        os.path.join(workspace_dir_path, f'farm_results{varroa_fragment}'))
    records = get_records(farm_results.records(), farm_results.fields)
    return records


def add_year_to_record(year, record):
    record[year_key] = year


def set_reveg_flag(flag, record):
    record['has_reveg'] = flag


def set_varroa_flag(flag, record):
    record['is_varroa'] = flag


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


def do_no_reveg_runs(farm_vector_path, landcover_raster_path, workspace_dir,
                     output_queue, crop_type, varroa_mite_year, total_years):
    try:
        logger.debug('processing year 0')
        year0_workspace_dir_path = os.path.join(workspace_dir, 'year0')
        os.mkdir(year0_workspace_dir_path)
        bp_table = build_no_reveg_biophys_table(crop_type)
        debug_dump_bp_table(bp_table, 0)
        year0_biophys_table_path = os.path.join(
            year0_workspace_dir_path, 'landcover_biophysical_table.csv')
        fill_in_and_write(bp_table, year0_biophys_table_path)

        def run_and_set_varroa_as(is_varroa):
            return run_natcap_pollination(farm_vector_path,
                                          year0_biophys_table_path,
                                          landcover_raster_path,
                                          year0_workspace_dir_path, crop_type,
                                          is_varroa)

        def yv_mapper(year, is_varroa):
            def result(e):
                add_year_to_record(year, e)
                set_reveg_flag(False, e)  # these runs are the "no reveg" ones
                set_varroa_flag(is_varroa, e)
                return e
            return result

        # year 0 records
        year0_records = run_and_set_varroa_as(False)
        year0_no_varroa_recs = map(yv_mapper(0, False), year0_records)
        # note: we make copies of lots of records to make the client's life
        # easier when it comes to charting. There's no out-of-band knowledge
        # required to be able to chart the results.
        # note: we assume varroa won't hit in year 0
        year0_varroa_recs = map(
            yv_mapper(0, True), deepcopy(year0_records))

        year_before_varroa = varroa_mite_year - 1
        if year_before_varroa > 0:
            # we need this so the chart has the sudden drop for varroa
            year_before_varroa_recs = map(
                yv_mapper(year_before_varroa, True), deepcopy(year0_records))
        else:
            year_before_varroa_recs = []

        # varroa year records
        raw_year_varroa_records = run_and_set_varroa_as(True)
        year_varroa_recs = map(
            yv_mapper(varroa_mite_year, True), raw_year_varroa_records)

        # final year records
        year_final_no_varroa_recs = map(
            yv_mapper(total_years, False), deepcopy(year0_records))
        year_final_varroa_recs = map(
            yv_mapper(total_years, True), deepcopy(raw_year_varroa_records))
        result = list(year0_no_varroa_recs) + \
            list(year0_varroa_recs) + \
            list(year_before_varroa_recs) + \
            list(year_varroa_recs) + \
            list(year_final_no_varroa_recs) + \
            list(year_final_varroa_recs)
        output_queue.put(result)
    except Exception:
        logger.exception(
            'Failed while processing year 0')  # stack trace will be included
        output_queue.put(FAILURE_FLAG)


def build_no_reveg_biophys_table(crop_type):
    """ Build biophysical table for run with no reveg.
    We need to chomp the reveg vector out of the farm vector so allow the reveg
    lucode to show through during reveg runs. However, during no reveg runs, we
    would just have the underlying lucode show through, which is not correct.
    Here we set the biophys table values for the reveg vector to what the farm
    is so the run is as-if the farm covers everything. The only caveat is that
    the model won't calculate yield for that chomped out piece."""
    base_landcover_bp_table_path = landcover_biophys_table_path(crop_type)
    bp_table = read_biophys_table_from_file(base_landcover_bp_table_path)
    fat_row = load_farm_attributes(crop_type)
    prefix = 'fr_'
    fr_col_keys = list(filter(lambda x: x.startswith(prefix), fat_row.keys()))
    if len(fr_col_keys) != 1:
        raise ValueError(f'Data error: expecting exactly 1 {prefix} column')
    fr_season_col_val = fat_row[fr_col_keys[0]]
    reveg_row = [reveg_lucode, fat_row['n_cavity'], fat_row['n_ground'],
                 fr_season_col_val]
    return append_to_2d_np(bp_table, reveg_row)


def run_future_year(farm_vector_path, landcover_raster_path, workspace_dir,
                    year_number, output_queue, crop_type, varroa_mite_year):
    try:
        logger.debug(f'processing year {year_number}')
        year_workspace_dir_path = os.path.join(workspace_dir,
                                               f'year{year_number}')
        os.mkdir(year_workspace_dir_path)
        bp_table = build_biophys_table(crop_type, year_number)
        debug_dump_bp_table(bp_table, year_number)
        curr_year_landcover_bp_table_path = os.path.join(
            year_workspace_dir_path, 'landcover_biophysical_table.csv')
        fill_in_and_write(bp_table, curr_year_landcover_bp_table_path)

        def run_and_set_varroa_as(is_varroa):
            return run_natcap_pollination(farm_vector_path,
                                          curr_year_landcover_bp_table_path,
                                          landcover_raster_path,
                                          year_workspace_dir_path, crop_type,
                                          is_varroa)

        records = []

        def no_varroa_mapper(e):
            set_varroa_flag(False, e)
            set_reveg_flag(True, e)
            add_year_to_record(year_number, e)
            return e

        records += map(no_varroa_mapper, run_and_set_varroa_as(False))

        def varroa_mapper(e):
            set_varroa_flag(True, e)
            set_reveg_flag(True, e)
            add_year_to_record(year_number, e)
            return e

        has_varroa_mite_hit = year_number >= varroa_mite_year
        if has_varroa_mite_hit:
            varroa_records = run_and_set_varroa_as(True)
            records += map(varroa_mapper, varroa_records)
        else:
            # duplicate the non-varroa result for client's benefit
            records += map(varroa_mapper, deepcopy(records))
        output_queue.put(records)
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
    result_path = os.path.join(year_workspace_dir_path,
                               'landcover_raster_with_reveg.tif')
    with open(year0_raster_path, 'rb') as f:
        data = f.read()
    with open(result_path, 'wb') as f:
        f.write(data)
    reprojected_reveg_vector_path = reproject_geojson_to_epsg3107(
        year_workspace_dir_path, reveg_vector)
    run_subprocess([
        '/usr/bin/gdal_rasterize', '-burn',
        str(reveg_lucode), '-l', KNOWN_REVEG_LAYER_NAME,
        reprojected_reveg_vector_path, result_path
    ])
    return result_path


def reproject_geojson_to_epsg3107(workspace_dir_path, reveg_geojson):
    reveg_vector_path = os.path.join(workspace_dir_path,
                                     KNOWN_REVEG_LAYER_NAME + '.json')
    with open(reveg_vector_path, 'w') as f:
        f.write(dumps(reveg_geojson))
    result_path = os.path.join(workspace_dir_path, reproj_reveg_filename)
    crs = get_crs_from_geojson(reveg_geojson)
    run_subprocess([
        '/usr/bin/ogr2ogr', '-s_srs', crs, '-t_srs', 'EPSG:3107', '-f',
        'GeoJSON', result_path, reveg_vector_path
    ])
    return result_path


def generate_images(workspace_dir, landcover_raster_path, farm_vector_path):
    """ generates the images and reads in the bytes of each image """
    result = {}
    farm_on_raster_path = os.path.join(workspace_dir,
                                       'landcover_and_farm.png')
    burn_vector_script_path = os.path.join(app_docker_dir_path,
                                           'burn-vector-to-raster-png.sh')
    # TODO we're using the chomped farm raster here. Perhaps we should burn the
    # reveg over the top, but colour it like the farm, which shows how we treat
    # the "no reveg" runs.
    run_subprocess([
        burn_vector_script_path, landcover_raster_path,
        farm_on_raster_path, farm_vector_path, farm_layer_and_file_name,
        str(farm_lucode)
    ])
    with open(farm_on_raster_path, 'rb') as f1:
        result['base'] = base64.b64encode(f1.read()).decode('utf-8')
    reveg_vector_path = os.path.join(workspace_dir, reproj_reveg_filename)
    is_only_year0_run = not os.path.isfile(reveg_vector_path)
    if is_only_year0_run:
        return result
    reveg_and_farm_on_raster_path = os.path.join(
        workspace_dir, 'landcover_and_farm_and_reveg.png')
    run_subprocess([
        burn_vector_script_path,
        farm_on_raster_path.replace('.png', '.tif'),
        reveg_and_farm_on_raster_path, reveg_vector_path,
        KNOWN_REVEG_LAYER_NAME, str(reveg_lucode)
    ])
    with open(reveg_and_farm_on_raster_path, 'rb') as f2:
        result['reveg'] = base64.b64encode(f2.read()).decode('utf-8')
    return result


def create_cropped_raster(farm_vector_path, workspace_dir):
    vector_extent = get_extent(farm_vector_path)
    full_raster_path = os.path.join(data_dir_path,
                                    u'south_australia_landcover.tif.gz')
    cropped_raster_path = os.path.join(workspace_dir, 'landcover_cropped.tif')
    run_subprocess(
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
        ])
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
        rows = list(reader)
    row_count = len(rows)
    if row_count != 1:
        logger.warn('Data error: Incorrect number of farm attribute rows' +
                    f'found={row_count} for crop {crop_type}. Must be ' +
                    'exactly 1!')
    return rows[0]


def transform_geojson_to_shapefile(geojson_vector_from_user, filename_fragment,
                                   workspace_dir, crop_type):
    """ Writes the supplied GeoJSON to a file, then transforms it
        to a shapefile and returns the path to that shapefile """
    shapefile_path = os.path.join(workspace_dir, filename_fragment + u'.shp')
    geojson_path = os.path.join(workspace_dir, filename_fragment + u'.json')
    row = load_farm_attributes(crop_type)
    row['crop_type'] = crop_type
    baked_geojson_vector = deepcopy(geojson_vector_from_user)
    # We only support a single polygon from the user. To support multiple
    # features/MultiPolygons we have to add logic that can draw the reveg in
    # the middle of *each* vector.
    baked_geojson_vector['features'][0]['properties'] = row
    crs = get_crs_from_geojson(geojson_vector_from_user)
    with open(geojson_path, 'w') as f:
        f.write(dumps(baked_geojson_vector))
    run_subprocess([
        '/usr/bin/ogr2ogr', '-s_srs', crs, '-t_srs', 'EPSG:3107', '-f',
        'ESRI Shapefile', shapefile_path, geojson_path
    ])
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
                       mark_year_as_done_fn, varroa_mite_year):
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
        farm_vector_path = farm_vector_minus_reveg_path
        cropped_landcover_raster_path = landcover_raster_cropper_fn(
            farm_vector_path, workspace_dir)
        landcover_raster_path = burn_reveg_on_raster(
            cropped_landcover_raster_path, geojson_reveg_vector,
            workspace_dir)

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
            pool.apply_async(do_no_reveg_runs,
                             (farm_vector_path, landcover_raster_path,
                              workspace_dir, output, crop_type,
                              varroa_mite_year, years_to_simulate)))
        for curr_year in subset_of_years(years_to_simulate, varroa_mite_year):
            processes.append(
                pool.apply_async(run_future_year,
                                 (farm_vector_minus_reveg_path,
                                     landcover_raster_path, workspace_dir,
                                     curr_year, output, crop_type,
                                     varroa_mite_year)))
        records = []
        pool.close()
        # we don't pool.join(), instead we block on the results in the queue so
        # we can fire notifications as processes finish. We trust that once we
        # have all the results, all the processes are finished.
        for p in processes:
            process_result = output.get()
            if process_result == FAILURE_FLAG:
                raise RuntimeError('Failed while executing the model')
            mark_year_as_done_fn()
            records += process_result
        records.sort(key=lambda x: x[year_key])
        result = {
            'images':
            generate_images(workspace_dir, cropped_landcover_raster_path,
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
