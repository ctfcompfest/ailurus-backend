from ailurus import create_worker_daemon
from ailurus.models import db, Config
from pytest_rabbitmq import factories as rabbitmq_factories
import pytest
from pika import BlockingConnection
from unittest.mock import patch


@pytest.fixture
def worker_daemon():
    rabbitmq_proc = rabbitmq_factories.rabbitmq_proc(port=59898, logsdir='/tmp')
    rabbitmq_factories.rabbitmq("rabbitmq_proc")

    app = create_worker_daemon(env_file=".env.tests")
    with app.app_context():
        db.create_all()

        cfg = [Config(key="ADMIN_SECRET", value="test"),
            Config(key="WORKER_SECRET", value="test")]
        db.session.add_all(cfg)
        db.session.commit()

        yield app
            
        db.session.remove()
        db.drop_all()

def test_worker(worker_daemon):
    pass