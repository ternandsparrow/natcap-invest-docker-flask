import time
import os
import shutil

import natcap.invest.pollination
import shapefile
import subprocess32 as subprocess
from flask import abort
from flask.json import dumps

from .invest_http_flask import SomethingFailedException
from .helpers import get_records, extract_min_max


def workspace_path(suffix):
    return u'/workspace/' + str(suffix)


def now_in_ms():
    return str(int(round(time.time() * 1000.0)))


def debug(msg):
    print('[DEBUG] %s' % msg)


class NatcapModelRunner(object):
    def execute_model(self, geojson_farm_vector):
        unique_workspace = now_in_ms() # FIXME might not be unique with parallel requests
        workspace_dir = workspace_path(unique_workspace)
        debug('using workspace dir "%s"' % workspace_dir)
        os.mkdir(workspace_dir)
        farm_vector_path = self.transform_geojson_to_shapefile(geojson_farm_vector, workspace_dir)
        args = {
            u'farm_vector_path': farm_vector_path,
            u'guild_table_path': u'/data/pollination/guild_table.csv',
            u'landcover_biophysical_table_path': u'/data/pollination/landcover_biophysical_table.csv',
            u'landcover_raster_path': u'/data/pollination/landcover.tif',
            u'results_suffix': u'',
            u'workspace_dir': workspace_dir,
        }
        natcap.invest.pollination.execute(args)
        shutil.rmtree(os.path.join(workspace_dir, u'intermediate_outputs'))
        farm_results = shapefile.Reader(os.path.join(workspace_dir, u'farm_results'))
        records = get_records(farm_results.records(), farm_results.fields)
        images = ['/image/' + unique_workspace + '/' + x.replace('.tif', '.png')
            for x in os.listdir(workspace_dir) if x.endswith('.tif')]
        return {
            'images': images,
            'records': records
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
    

    def get_png(self, uniqueworkspace, imagename):
        resize_percentage = '40%'
        workspace_dir = workspace_path(uniqueworkspace)
        png_file_path = os.path.join(workspace_dir, imagename)
        tiff_file_path = png_file_path.replace('.png', '.tif')
        if not os.path.isfile(tiff_file_path):
            raise SomethingFailedException(abort(404)) # guard for requesting non-existing files
        if not imagename.endswith('.png'):
            raise SomethingFailedException(abort(400)) # TODO add message that only PNG is supported
        if os.path.isfile(png_file_path):
            return png_file_path
        debug('generating PNG from "%s"' % tiff_file_path)
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
