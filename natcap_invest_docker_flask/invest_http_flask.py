from flask import Flask, jsonify, send_file, render_template, request
from flask_cors import CORS

# Inject this dependency. FIXME can we create a class and pass this to the constructor?
# model_runner = None
def make_app(model_runner):
    app = Flask(__name__)
    CORS(app)
    # stop Jinja2/angularjs conflict, thanks https://stackoverflow.com/a/30362956/1410035
    jinja_options = app.jinja_options.copy()

    jinja_options.update(dict(
        variable_start_string='{j{',
        variable_end_string='}j}',
    ))
    app.jinja_options = jinja_options

    @app.route('/')
    def root():
        return jsonify({
            '_links': [
                {'rel': 'pollination', 'href': '/pollination'},
                {'rel': 'tester-ui', 'href': '/tester'}
            ]
        })

    @app.route('/pollination')
    def pollination():
        """ executes the InVEST pollination model and returns the results """
        result = model_runner.execute_model()
        return jsonify(result)

    # FIXME handle double slashes
    @app.route('/image/<uniqueworkspace>/<imagename>')
    def get_png(uniqueworkspace, imagename):
        """ fetches the PNG version of a GeoTIFF in a lazy-init way """
        try:
            png_file_path = model_runner.get_png(uniqueworkspace, imagename)
            return send_file(png_file_path, mimetype='image/png')
        except SomethingFailedException as e:
            return e.http_resp

    # TODO add endpoint to retrieve GeoTIFF images

    @app.route('/tester')
    def tester():
        """ returns a UI for interacting with this service """
        return render_template('testerui.html', url_root=request.url_root)

    return app


class SomethingFailedException(Exception):
  def __init__(self, http_resp):
    super(SomethingFailedException, self).__init__()
    self.http_resp = http_resp
