from ailurus import create_webapp_daemon

import flask_migrate
from gevent import monkey
monkey.patch_all()

app = create_webapp_daemon()
with app.app_context():
    flask_migrate.upgrade()