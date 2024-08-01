from ailurus import create_webapp_daemon
from ailurus.models import db, Config
from flask import Flask
import pytest

@pytest.fixture
def webapp():
    app = create_webapp_daemon(env_file=".env.tests")
    with app.app_context():
        db.create_all()

        cfg = [Config(key="ADMIN_SECRET", value="test"),
               Config(key="WORKER_SECRET", value="test"),
                Config(key="CORS_WHITELIST", value="[\"https://localhost\"]")]
        db.session.add_all(cfg)
        db.session.commit()

        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(webapp: Flask):
    return webapp.test_client()