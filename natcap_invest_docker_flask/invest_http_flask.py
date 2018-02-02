import time
import os
import shutil

from flask import Flask, jsonify, abort, send_file, render_template, request
from flask_cors import CORS
import natcap.invest.pollination
import shapefile
import subprocess32 as subprocess

from helpers import get_records, extract_min_max

app = Flask(__name__)
CORS(app)
# stop Jinja2/angularjs conflict, thanks https://stackoverflow.com/a/30362956/1410035
jinja_options = app.jinja_options.copy()

jinja_options.update(dict(
    variable_start_string='{j{',
    variable_end_string='}j}',
))
app.jinja_options = jinja_options

def workspace_path(suffix):
    return u'/workspace/' + str(suffix)

def now_in_ms():
    return str(int(round(time.time() * 1000.0)))

def debug(msg):
    print('[DEBUG] %s' % msg)

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
    debug('using workspace dir "%s"' % workspace_dir)
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
    records = get_records(farm_results.records(), farm_results.fields)
    images = ['/image/' + unique_workspace + '/' + x.replace('.tif', '.png')
        for x in os.listdir(workspace_dir) if x.endswith('.tif')]
    return jsonify({
        'images': images,
        'records': records
    })

# FIXME handle double slashes
@app.route("/image/<uniqueworkspace>/<imagename>")
def get_png(uniqueworkspace, imagename):
    """ fetches the PNG version of a GeoTIFF in a lazy-init way """
    resize_percentage = '40%'
    workspace_dir = workspace_path(uniqueworkspace)
    png_file = os.path.join(workspace_dir, imagename)
    tiff_file = png_file.replace('.png', '.tif')
    if not os.path.isfile(tiff_file):
        return abort(404) # guard for requesting non-existing files
    if not imagename.endswith('.png'):
        return abort(400) # TODO add message that only PNG is supported
    if os.path.isfile(png_file):
        return send_file(png_file, mimetype='image/png')
    debug('generating PNG from "%s"' % tiff_file)
    shelloutput = subprocess.check_output('gdalinfo %s | grep "Min="' % tiff_file, shell=True)
    minmax = extract_min_max(shelloutput)
    min_scale = minmax['min']
    max_scale = minmax['max']
    # Our version of gdal (1.11.x) is too old to have translate() and info(), only >2 seems to have that.
    # So we resort to using the shell commands that give us the functionality.
    subprocess.check_call([
        '/usr/bin/gdal_translate',
        '-of', 'PNG',
        '-ot', 'Byte',
        '-scale', min_scale, max_scale,
        '-outsize', resize_percentage, resize_percentage,
        tiff_file,
        png_file], stdout=subprocess.DEVNULL)
    return send_file(png_file, mimetype='image/png')

# TODO add endpoint to retrieve GeoTIFF images

@app.route('/tester')
def tester():
    """ returns a UI for interacting with this service """
    return render_template('testerui.html', url_root=request.url_root)
