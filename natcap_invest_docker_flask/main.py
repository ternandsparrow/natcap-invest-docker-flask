import os
import sys
from flask_socketio import SocketIO
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from natcap_invest_docker_flask import AppBuilder, natcap_wrapper  # noqa E402

socketio_secret = os.getenv('SOCKETIO_SECRET', default='secret!')
app_builder = AppBuilder(natcap_wrapper.NatcapModelRunner())
app = app_builder.build()
app.config['SECRET_KEY'] = socketio_secret
socketio = SocketIO(app)
app_builder.set_socketio(socketio)

is_debug = True
nidf_env = os.getenv('NIDF_ENV', default='development')
if nidf_env == 'production':
    is_debug = False

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=is_debug)
