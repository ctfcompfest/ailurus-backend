from ailurus.utils.config import get_config, set_config
from flask.testing import FlaskClient
import pytest
import json
import datetime
from unittest.mock import Mock, patch

@pytest.fixture
def config_fixtures():
    set_config("EVENT_NAME", "Contest Name")
    set_config("TICK_DURATION", "10")
    set_config("CORS_WHITELIST", json.dumps([]))

def test_get_configs(client: FlaskClient, config_fixtures):
    response = client.get("/api/v2/admin/configs/", headers={"X-ADMIN-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()['data']
    print(response_data)
    for key in ["EVENT_NAME", "CORS_WHITELIST", "TICK_DURATION", "ADMIN_SECRET"]:
        assert key in response_data

def test_patch_configs(client: FlaskClient, config_fixtures):
    response = client.patch("/api/v2/admin/configs/EVENT_NAME/", headers={"X-ADMIN-SECRET": "test"}, json={"value": "Test Contest"})
    assert response.status_code == 200
    assert get_config("EVENT_NAME") == "Test Contest"

    response = client.patch("/api/v2/admin/configs/TICK_DURATION/", headers={"X-ADMIN-SECRET": "test"}, json={"value": 5})
    assert response.status_code == 200
    assert get_config("TICK_DURATION") == 5

    response = client.patch(
        "/api/v2/admin/configs/CORS_WHITELIST/",
        headers={"X-ADMIN-SECRET": "test", "Origin": "https://random.random"},
        json={"value": ["https://random.random"]}
    )
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "https://random.random"
    
    response = client.get("/api/v2/admin/configs/", headers={"X-ADMIN-SECRET": "test", "Origin": "https://other.other"})
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == None

def test_fail_patch_configs(client: FlaskClient, config_fixtures):
    response = client.patch("/api/v2/admin/configs/NONEXIST_KEY/", headers={"X-ADMIN-SECRET": "test"}, json={"value": "Test Contest"})
    assert response.status_code == 404
    assert response.get_json()['message'] == "configuration key not found."

    response = client.patch("/api/v2/admin/configs/EVENT_NAME/", headers={"X-ADMIN-SECRET": "test"}, json={"key": "Test Contest"})
    assert response.status_code == 400
    assert response.get_json()['message'] == "missing 'value' key in body request."

@patch("ailurus.utils.contest.datetime")
def test_path_paused_configs(mock_datetime, client: FlaskClient, config_fixtures):
    mock_datetime.now.return_value = datetime.datetime(year=2020, month=10, day=10, hour=10, minute=20, second=12, tzinfo=datetime.timezone.utc)
    set_config("IS_CONTEST_PAUSED", False)
    response = client.patch(
        "/api/v2/admin/configs/IS_CONTEST_PAUSED/",
        headers={"X-ADMIN-SECRET": "test"},
        json={"value": True}
    )
    assert response.status_code == 200
    assert get_config("IS_CONTEST_PAUSED") == True
    assert get_config("LAST_PAUSED") == datetime.datetime(year=2020, month=10, day=10, hour=10, minute=20, tzinfo=datetime.timezone.utc)

    response = client.patch(
        "/api/v2/admin/configs/IS_CONTEST_PAUSED/",
        headers={"X-ADMIN-SECRET": "test"},
        json={"value": "false"}
    )
    assert response.status_code == 200
    assert get_config("IS_CONTEST_PAUSED") == False

    set_config("IS_CONTEST_PAUSED", True)
    set_config("LAST_TICK_CHANGE", "2020-10-10T10:10:00Z")
    set_config("LAST_PAUSED", "2020-10-10T10:13:00Z")
    
    response = client.patch(
        "/api/v2/admin/configs/IS_CONTEST_PAUSED/",
        headers={"X-ADMIN-SECRET": "test"},
        json={"value": False}
    )
    assert response.status_code == 200
    assert get_config("IS_CONTEST_PAUSED") == False
    assert get_config("LAST_TICK_CHANGE") == datetime.datetime(year=2020, month=10, day=10, hour=10, minute=17, tzinfo=datetime.timezone.utc)
