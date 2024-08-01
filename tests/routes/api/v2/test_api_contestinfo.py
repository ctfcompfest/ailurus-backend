from ailurus.utils.config import set_config
from flask.testing import FlaskClient
import pytest
from datetime import datetime, timezone, timedelta

@pytest.fixture
def config_data():
    set_config("EVENT_NAME", "My Event")
    set_config("LOGO_URL", "")
    set_config("NUMBER_ROUND", "3")
    set_config("NUMBER_TICK", "3")
    set_config("START_TIME", "3000-01-01T01:00:00+00:00")
    set_config("IS_CONTEST_PAUSED", "false")

@pytest.fixture
def contest_started():
    start_time = datetime.now(timezone.utc) - timedelta(days=1)
    set_config("START_TIME", start_time.isoformat())

def test_evenstatus_timenow_less_starttime(client: FlaskClient, config_data):
    # time now < start time
    resp = client.get("/api/v2/contest/info/")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["event_status"] == "not started"

def test_evenstatus_timenow_less_starttime_and_paused(client: FlaskClient, config_data):
    # time now < start time and is_contest_paused = true
    set_config("IS_CONTEST_PAUSED", "true")
    resp = client.get("/api/v2/contest/info/")
    assert resp.get_json()["data"]["event_status"] == "not started"

def test_evenstatus_timenow_less_starttime_and_currentround_more_numround(client: FlaskClient, config_data):
    # time now < start time and current round > number round
    set_config("CURRENT_ROUND", "4")
    resp = client.get("/api/v2/contest/info/")
    assert resp.get_json()["data"]["event_status"] == "not started"

def test_eventstatus_started_and_paused(client: FlaskClient, config_data, contest_started):
    # time now >= start time and is_contest_paused = true
    set_config("IS_CONTEST_PAUSED", "true")
    resp = client.get("/api/v2/contest/info/")
    assert resp.get_json()["data"]["event_status"] == "paused"

def test_eventstatus_started_and_notpaused(client: FlaskClient, config_data, contest_started):
    # time now >= start time and is_contest_paused = true
    set_config("IS_CONTEST_PAUSED", "false")
    resp = client.get("/api/v2/contest/info/")
    assert resp.get_json()["data"]["event_status"] == "running"

def test_eventstatus_started_notpaused_currentround_more(client: FlaskClient, config_data, contest_started):
    # time now >= start time and is_contest_paused = true
    set_config("CURRENT_ROUND", "4")
    resp = client.get("/api/v2/contest/info/")
    assert resp.get_json()["data"]["event_status"] == "finished"

def test_eventstatus_started_paused_currentround_more(client: FlaskClient, config_data, contest_started):
    # time now >= start time and is_contest_paused = true
    set_config("IS_CONTEST_PAUSED", "true")
    set_config("CURRENT_ROUND", "4")
    resp = client.get("/api/v2/contest/info/")
    assert resp.get_json()["data"]["event_status"] == "finished"