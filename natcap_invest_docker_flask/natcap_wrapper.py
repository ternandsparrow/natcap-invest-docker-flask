import time
import os
import shutil
import logging

import natcap.invest.pollination
import shapefile
import subprocess32 as subprocess
import osgeo.ogr as ogr
import osgeo.osr as osr
import numpy as np
from flask import abort
from flask.json import dumps

from .invest_http_flask import SomethingFailedException
from .helpers import get_records, extract_min_max

logger = logging.getLogger('natcap_wrapper')
pygeo_logger = logging.getLogger('pygeoprocessing.geoprocessing')
pygeo_logger.setLevel(logging.WARN)

# TODO make env var configurable
data_dir_path = u'/data/pollination'
workspace_parent_dir_path = u'/workspace/'
metres_of_padding_for_crop = 3000
reveg_lucode = 1337


def workspace_path(suffix):
    return os.path.join(workspace_parent_dir_path, str(suffix))


def now_in_ms():
    return int(round(time.time() * 1000.0))


def generate_unique_token():
    return str(now_in_ms()) # FIXME not unique with parallel requests


def get_biophysical_table_row_for_year(year):
    # TODO need to work out the logic for this with scientists
    v = 0.1 * year
    return [[reveg_lucode, v, v, v, v]]


def run_natcap_pollination(farm_vector_path, landcover_biophysical_table_path,
        landcover_raster_path, workspace_dir_path, is_keep_images):
    args = {
        u'farm_vector_path': farm_vector_path,
        u'guild_table_path': os.path.join(data_dir_path, u'guild_table.csv'),
        u'landcover_biophysical_table_path': landcover_biophysical_table_path,
        u'landcover_raster_path': landcover_raster_path,
        u'results_suffix': u'',
        u'workspace_dir': workspace_dir_path,
    }
    natcap.invest.pollination.execute(args)
    shutil.rmtree(os.path.join(workspace_dir_path, u'intermediate_outputs'))
    farm_results = shapefile.Reader(os.path.join(workspace_dir_path, u'farm_results'))
    records = get_records(farm_results.records(), farm_results.fields)
    if not is_keep_images:
        images = [x for x in os.listdir(workspace_dir_path) if x.endswith('.tif')]
        for curr in images:
            try:
                curr_path = os.path.join(workspace_dir_path, curr)
                os.remove(curr_path)
            except Exception as e:
                logger.error('failed to remove image %s, cause "%s"' % (curr, str(e)))
    return records


def append_records(record_collector, new_records, year_number):
    for curr in new_records:
        curr.update({'year': year_number})
        record_collector.append(curr)


class NatcapModelRunner(object):
    def execute_model(self, geojson_farm_vector, years_to_simulate, geojson_reveg_vector):
        start_ms = now_in_ms()
        unique_workspace = generate_unique_token()
        workspace_dir = workspace_path(unique_workspace)
        logger.debug('using workspace dir "%s"' % workspace_dir)
        os.mkdir(workspace_dir)
        farm_vector_path = self.transform_geojson_to_shapefile(geojson_farm_vector, workspace_dir)
        reveg_vector_path = None # use geojson_reveg_vector, figure out what we need to mask the raster
        landcover_raster_path = self.create_cropped_raster(farm_vector_path, workspace_dir)
        records = []
        year0_records = self.run_year0(farm_vector_path, landcover_raster_path, workspace_dir)
        append_records(records, year0_records, 0)
        for curr_year in range(1, years_to_simulate + 1):
            is_keep_images = curr_year == years_to_simulate
            year_records = self.run_future_year(farm_vector_path, landcover_raster_path,
                    workspace_dir, curr_year, is_keep_images, reveg_vector_path)
            append_records(records, year_records, curr_year)
        images = [] # TODO what do we want to return? year0 raster with farm shown and final year raster with farm and reveg?
        #     os.path.join('/image', unique_workspace, x.replace('.tif', '.png'))
        #     for x in os.listdir(workspace_dir)
        #     if (x.endswith('.tif') and not x == 'landcover_cropped.tif')
        # ]
        elapsed_ms = now_in_ms() - start_ms
        logger.debug('execution time %dms' % elapsed_ms)
        return {
            'images': images,
            'records': records
        }


    def run_year0(self, farm_vector_path, landcover_raster_path, workspace_dir):
        logger.debug('processing year 0')
        year0_workspace_dir_path = os.path.join(workspace_dir, 'year0')
        os.mkdir(year0_workspace_dir_path)
        landcover_bp_table_path = os.path.join(data_dir_path, u'landcover_biophysical_table.csv')
        records = run_natcap_pollination(farm_vector_path, landcover_bp_table_path,
            landcover_raster_path, year0_workspace_dir_path, True)
        return records


    def run_future_year(self, farm_vector_path, landcover_raster_path, workspace_dir, year_number, is_keep_images, reveg_vector_path):
        logger.debug('processing year %s' % str(year_number))
        year_workspace_dir_path = os.path.join(workspace_dir, 'year' + str(year_number))
        os.mkdir(year_workspace_dir_path)
        base_landcover_bp_table_path = os.path.join(data_dir_path, u'landcover_biophysical_table.csv')
        bp_table = np.loadtxt(base_landcover_bp_table_path, skiprows=1, delimiter=',')
        new_row = get_biophysical_table_row_for_year(year_number)
        new_bp_table = np.concatenate((bp_table, new_row), axis=0)
        landcover_bp_table_path = os.path.join(year_workspace_dir_path, 'landcover_biophysical_table.csv')
        with open(base_landcover_bp_table_path) as f:
            bp_table_header = f.readline()
        with open(landcover_bp_table_path, 'w') as f:
            f.write(bp_table_header)
            np.savetxt(f, new_bp_table, fmt='%d,%.6f,%.6f,%.6f,%.6f')
        new_landcover_raster_path = os.path.join(year_workspace_dir_path, 'landcover_raster.tif')
        self.add_reveg_to_raster(landcover_raster_path, new_landcover_raster_path, reveg_vector_path)
        records = run_natcap_pollination(farm_vector_path, landcover_bp_table_path,
            new_landcover_raster_path, year_workspace_dir_path, is_keep_images)
        return records


    def add_reveg_to_raster(self, year0_raster_path, new_raster_path, reveg_vector):
        # TODO adjust pixels in raster
        data = None
        with open(year0_raster_path, 'r') as f:
            data = f.read()
        with open(new_raster_path, 'w') as f:
            f.write(data)


    def create_cropped_raster(self, farm_vector_path, workspace_dir):
        vector_extent = self.get_extent(farm_vector_path)
        full_raster_path = os.path.join(data_dir_path, u'south_australia_landcover.tif.gz')
        cropped_raster_path = os.path.join(workspace_dir, 'landcover_cropped.tif')
        subprocess.check_call([
            '/usr/bin/gdal_translate',
            '-projwin', # probably specific to southern hemisphere and Australia's side of 0 degree longitude
                vector_extent['x_min'],
                vector_extent['y_max'],
                vector_extent['x_max'],
                vector_extent['y_min'],
            '-of', 'GTiff',
            u'/vsigzip/' + full_raster_path,
            cropped_raster_path], stdout=subprocess.DEVNULL)
        return cropped_raster_path


    def get_extent(self, farm_vector_path):
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
            'x_min': str(x_min - metres_of_padding_for_crop),
            'y_min': str(y_min - metres_of_padding_for_crop),
            'y_max': str(y_max + metres_of_padding_for_crop),
            'x_max': str(x_max + metres_of_padding_for_crop),
        }


    def transform_geojson_to_shapefile(self, geojson_farm_vector, workspace_dir):
        """ Writes the supplied GeoJSON to a file, then transforms it
            to a shapefile and returns the path to that shapefile """
        farm_vector_path = os.path.join(workspace_dir, u'farms.shp')
        geojson_path = os.path.join(workspace_dir, u'farms.json')
        with open(geojson_path, 'w') as f:
            f.write(dumps(geojson_farm_vector))
        subprocess.check_call([
            '/usr/bin/ogr2ogr',
            '-f', 'ESRI Shapefile',
            farm_vector_path,
            geojson_path], stdout=subprocess.DEVNULL)
        return farm_vector_path
    

    def get_png(self, unique_workspace_fragment, imagename):
        resize_percentage = '40%'
        unique_workspace_path = workspace_path(unique_workspace_fragment)
        png_file_path = os.path.join(unique_workspace_path, imagename)
        tiff_file_path = png_file_path.replace('.png', '.tif')
        if not os.path.isfile(tiff_file_path):
            raise SomethingFailedException(abort(404)) # guard for requesting non-existing files
        if not imagename.endswith('.png'):
            raise SomethingFailedException(abort(400)) # TODO add message that only PNG is supported
        if os.path.isfile(png_file_path):
            return png_file_path
        logger.debug('generating PNG from "%s"' % tiff_file_path)
        shelloutput = subprocess.check_output('gdalinfo %s | grep "Min="' % tiff_file_path, shell=True)
        minmax = extract_min_max(shelloutput)
        min_scale = minmax['min']
        max_scale = minmax['max']
        # Our version of gdal (v1.11.x) is too old to have translate() and info()
        # binding in the python API, only >v2 seems to have that.
        # So we resort to using the shell commands that give us the functionality.
        subprocess.check_call([
            '/usr/bin/gdal_translate',
            '-of', 'PNG',
            '-ot', 'Byte',
            '-scale', min_scale, max_scale,
            '-outsize', resize_percentage, resize_percentage,
            tiff_file_path,
            png_file_path], stdout=subprocess.DEVNULL)
        return png_file_path
