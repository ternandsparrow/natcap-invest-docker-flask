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

# note: this 'debug' param is not just about debugging, but also about
# hot-reload on code change. See
# https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.debug
is_debug = True
nidf_env = os.getenv('NIDF_ENV', default='development')
if nidf_env == 'production':
    is_debug = False

ptvsd_enable = os.getenv('PTVSD_ENABLE', default=0)
extra_run_args={}
if ptvsd_enable == '1':
    print('[INFO] Remote debugging, via ptvsd, is enabled')
    # we need to do this so we can debug multiprocessing
    import multiprocessing
    multiprocessing.set_start_method('spawn', True)
    # somewhat following https://vinta.ws/code/remotely-debug-a-python-app-inside-a-docker-container-in-visual-studio-code.html
    import ptvsd
    ptvsd_port = int(os.getenv('P8_CHILD_DEBUG_PORT', default=3000))
    ptvsd.enable_attach(address=('0.0.0.0', ptvsd_port))
    is_debug = False # not compatible with remote debugging
    print('ptvsd is started (port=%d), waiting for you to attach...' % ptvsd_port)
    ptvsd.wait_for_attach()
    print('debugger is attached')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=is_debug)
