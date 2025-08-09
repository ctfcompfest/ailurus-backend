from ailurus import create_webapp_daemon

import socketio
import flask_migrate

webapp = create_webapp_daemon()
with webapp.app_context():
    flask_migrate.upgrade()
    
sio = socketio.Server(cors_allowed_origin="*", engineio_logger=True)
app = socketio.WSGIApp(sio, webapp)