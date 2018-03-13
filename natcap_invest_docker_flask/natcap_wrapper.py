import time
import os
import shutil
import logging
import base64

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
farm_lucode = 2000
farm_layer_and_file_name = u'farms'
reproj_reveg_filename = u'reprojected_reveg_geojson.json'


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
        landcover_raster_path = self.create_cropped_raster(farm_vector_path, workspace_dir)
        records = []
        year0_records = self.run_year0(farm_vector_path, landcover_raster_path, workspace_dir)
        append_records(records, year0_records, 0)
        for curr_year in range(1, years_to_simulate + 1):
            is_keep_images = curr_year == years_to_simulate
            year_records = self.run_future_year(farm_vector_path, landcover_raster_path,
                    workspace_dir, curr_year, is_keep_images, geojson_reveg_vector)
            append_records(records, year_records, curr_year)
        elapsed_ms = now_in_ms() - start_ms
        logger.debug('execution time %dms' % elapsed_ms)
        return {
            'images': self.generate_images(workspace_dir, landcover_raster_path, farm_vector_path),
            'records': records
        }


    def generate_images(self, workspace_dir, landcover_raster_path, farm_vector_path):
        """ generates the images and reads in the bytes of each image """
        result = {}
        year0_farm_on_raster_path = os.path.join(workspace_dir, 'landcover_and_farm.png')
        subprocess.check_call([
            '/app/burn-vector-to-raster-png.sh',
            landcover_raster_path,
            year0_farm_on_raster_path,
            farm_vector_path,
            farm_layer_and_file_name,
            str(farm_lucode)], stdout=subprocess.DEVNULL)
        with open(year0_farm_on_raster_path, 'rb') as f1:
            result['base'] = base64.b64encode(f1.read())
        reveg_vector_path = os.path.join(workspace_dir, 'year1', reproj_reveg_filename)
        is_only_year0_run = not os.path.isfile(reveg_vector_path)
        if is_only_year0_run:
            return result
        reveg_and_farm_on_raster_path = os.path.join(workspace_dir, 'landcover_and_farm_and_reveg.png')
        subprocess.check_call([
            '/app/burn-vector-to-raster-png.sh',
            year0_farm_on_raster_path.replace('.png', '.tif'),
            reveg_and_farm_on_raster_path,
            reveg_vector_path,
            'OGRGeoJSON',
            str(reveg_lucode)], stdout=subprocess.DEVNULL)
        with open(reveg_and_farm_on_raster_path, 'rb') as f2:
            result['reveg'] = base64.b64encode(f2.read())
        return result


    def run_year0(self, farm_vector_path, landcover_raster_path, workspace_dir):
        logger.debug('processing year 0')
        year0_workspace_dir_path = os.path.join(workspace_dir, 'year0')
        os.mkdir(year0_workspace_dir_path)
        landcover_bp_table_path = os.path.join(data_dir_path, u'landcover_biophysical_table.csv')
        records = run_natcap_pollination(farm_vector_path, landcover_bp_table_path,
            landcover_raster_path, year0_workspace_dir_path, True)
        return records


    def run_future_year(self, farm_vector_path, landcover_raster_path, workspace_dir, year_number, is_keep_images, reveg_vector):
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
        new_landcover_raster_path = self.burn_reveg_on_raster(landcover_raster_path, reveg_vector, year_workspace_dir_path)
        records = run_natcap_pollination(farm_vector_path, landcover_bp_table_path,
            new_landcover_raster_path, year_workspace_dir_path, is_keep_images)
        return records


    def burn_reveg_on_raster(self, year0_raster_path, reveg_vector, year_workspace_dir_path):
        """ clones the raster and burns the reveg landuse code into the clone using the vector """
        data = None
        result_path = os.path.join(year_workspace_dir_path, 'landcover_raster.tif')
        with open(year0_raster_path, 'r') as f:
            data = f.read()
        with open(result_path, 'w') as f:
            f.write(data)
        reveg_vector_path = os.path.join(year_workspace_dir_path, 'reveg_geojson.json')
        with open(reveg_vector_path, 'w') as f:
            f.write(dumps(reveg_vector))
        reprojected_reveg_vector_path = self.reproject_geojson_to_epsg3107(year_workspace_dir_path, reveg_vector_path)
        # feel the burn!
        subprocess.check_call([
            '/usr/bin/gdal_rasterize',
            '-burn', str(reveg_lucode),
            '-l', 'OGRGeoJSON',
            reprojected_reveg_vector_path,
            result_path], stdout=subprocess.DEVNULL)
        return result_path


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


    def reproject_geojson_to_epsg3107(self, workspace_dir_path, geojson_path):
        result_path = os.path.join(workspace_dir_path, reproj_reveg_filename)
        subprocess.check_call([
            '/usr/bin/ogr2ogr',
            '-s_srs', 'EPSG:4326', # assuming the incoming geojson has no CRS so WGS84 is implied
            '-t_srs', 'EPSG:3107',
            '-f', 'GeoJSON',
            result_path,
            geojson_path], stdout=subprocess.DEVNULL)
        return result_path

    def transform_geojson_to_shapefile(self, geojson_farm_vector, workspace_dir):
        """ Writes the supplied GeoJSON to a file, then transforms it
            to a shapefile and returns the path to that shapefile """
        farm_vector_path = os.path.join(workspace_dir, farm_layer_and_file_name + u'.shp')
        geojson_path = os.path.join(workspace_dir, farm_layer_and_file_name + u'.json')
        with open(geojson_path, 'w') as f:
            f.write(dumps(geojson_farm_vector))
        # TODO do we need to reproject GDA94 GeoJSON into EPSG:3107?
        subprocess.check_call([
            '/usr/bin/ogr2ogr',
            '-s_srs', 'EPSG:4326', # assuming the incoming geojson has no CRS so WGS84 is implied
            '-t_srs', 'EPSG:3107',
            '-f', 'ESRI Shapefile',
            farm_vector_path,
            geojson_path], stdout=subprocess.DEVNULL)
        return farm_vector_path
    