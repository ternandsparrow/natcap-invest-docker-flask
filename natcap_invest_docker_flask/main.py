import os
import sys
import logging
from flask_socketio import SocketIO
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from natcap_invest_docker_flask import AppBuilder, natcap_wrapper  # noqa E402
from natcap_invest_docker_flask.logger import logger_getter  # noqa E402

socketio_secret = os.getenv('SOCKETIO_SECRET', default='secret!')
app_builder = AppBuilder(natcap_wrapper.NatcapModelRunner())
app = app_builder.build()
app.config['SECRET_KEY'] = socketio_secret
cors_origin = os.getenv('CORS_ORIGIN', default='*')
socketio = SocketIO(app, cors_allowed_origins=cors_origin)
app_builder.set_socketio(socketio)

is_debug = True
nidf_env = os.getenv('NIDF_ENV', default='development')
if nidf_env == 'production':
    is_debug = False
    logger = logger_getter.get_app_logger()
    logger.setLevel(logging.INFO)
    logger.info('Logger set to INFO level')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=is_debug)
