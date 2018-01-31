from flask import Flask, jsonify, abort, send_file
import natcap.invest.pollination
import shapefile
import time
import os
import subprocess32 as subprocess
import shutil

app = Flask(__name__)

def workspace_path(suffix):
    return u'/workspace/' + str(suffix)

def now_in_ms():
    return str(int(round(time.time() * 1000.0)))

@app.route("/")
def hello():
    return jsonify({
        '_links': [
            {'rel': 'pollination', 'href': '/pollination'}
        ]
    })

@app.route("/pollination")
def pollination():
    """ executes the InVEST pollination model and returns the results """
    unique_workspace = now_in_ms() # FIXME might not be unique with parallel requests
    workspace_dir = workspace_path(unique_workspace)
    print('[DEBUG] using workspace dir "%s"' % workspace_dir)
    os.mkdir(workspace_dir)
    args = {
        u'farm_vector_path': u'/data/pollination/farms.shp',
        u'guild_table_path': u'/data/pollination/guild_table.csv',
        u'landcover_biophysical_table_path': u'/data/pollination/landcover_biophysical_table.csv',
        u'landcover_raster_path': u'/data/pollination/landcover.tif',
        u'results_suffix': u'',
        u'workspace_dir': workspace_dir,
    }
    natcap.invest.pollination.execute(args)
    shutil.rmtree(os.path.join(workspace_dir, u'intermediate_outputs'))
    farm_results = shapefile.Reader(os.path.join(workspace_dir, u'farm_results'))
    # TODO add field names for records
    records = farm_results.records()
    images = ['/image/' + unique_workspace + '/' + x.replace('.tif', '.png')
        for x in os.listdir(workspace_dir) if x.endswith('.tif')]
    return jsonify({
        'images': images,
        'records': records
    })

@app.route("/image/<uniqueworkspace>/<imagename>")
def get_png(uniqueworkspace, imagename):
    """ fetches the PNG version of a GeoTIFF in a lazy-init way """
    resize_percentage = '40%'
    workspace_dir = workspace_path(uniqueworkspace)
    png_file = os.path.join(workspace_dir, imagename)
    tiff_file = png_file.replace('.png', '.tif')
    if not os.path.isfile(tiff_file):
        return abort(404) # guard for requesting non-existing files
    if not (imagename.endswith('.png')):
        return abort(400) # TODO add message that only PNG is supported
    if os.path.isfile(png_file):
        return send_file(png_file, mimetype='image/png')
    subprocess.check_call([ # FIXME swallow the stdout
        '/usr/bin/gdal_translate',
        '-of', 'PNG',
        '-ot', 'Byte',
        '-scale', '0', '0.092', # FIXME dynamically read this
        '-outsize', resize_percentage, resize_percentage,
        tiff_file,
        png_file])
    return send_file(png_file, mimetype='image/png')

# TODO add endpoint to retrieve GeoTIFF images
