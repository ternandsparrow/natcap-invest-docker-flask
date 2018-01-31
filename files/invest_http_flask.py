from flask import Flask, jsonify
import natcap.invest.pollination
import shapefile
import time
import os

app = Flask(__name__)

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
    ms = int(round(time.time() * 1000.0))
    workspace_dir = u'/workspace/' + str(ms)
    print('using workspace dir "%s"' % workspace_dir)
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
    farm_results = shapefile.Reader(os.path.join(workspace_dir, u'farm_results'))
    records = farm_results.records()
    # TODO compress GeoTIFF to PNG with GDAL
    return jsonify({
        # TODO add links to images
        'records': records
    })

# TODO add endpoint to retrieve images, GeoTIFF and PNG
