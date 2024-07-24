from ailurus import create_app
from ailurus.models import db, Config
from flask import Flask
import pytest

@pytest.fixture
def app():
    app = create_app(env_file=".env.tests")
    with app.app_context():
        db.create_all()

        cfg = Config(key="ADMIN_SECRET", value="test")
        db.session.add(cfg)
        db.session.commit()

        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app: Flask):
    return app.test_client()