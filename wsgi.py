from gevent import monkey

from ailurus import create_webapp_daemon

import socketio
import flask_migrate

monkey.patch_all()

webapp = create_webapp_daemon()
with webapp.app_context():
    from ailurus.utils.socket import socketio
    
    flask_migrate.upgrade()
    
    app = socketio.WSGIApp(socketio, webapp)