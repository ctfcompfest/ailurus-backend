from ailurus.utils.config import get_config, set_config
from flask.testing import FlaskClient
import pytest
import json

@pytest.fixture
def config_fixtures():
    set_config("EVENT_NAME", "Contest Name")
    set_config("TICK_DURATION", "10")
    set_config("CORS_WHITELIST", json.dumps([]))

def test_get_configs(client: FlaskClient, config_fixtures):
    response = client.get("/api/v2/admin/configs/", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()['data']
    print(response_data)
    for key in ["EVENT_NAME", "CORS_WHITELIST", "TICK_DURATION", "ADMIN_SECRET"]:
        assert key in response_data

def test_patch_configs(client: FlaskClient, config_fixtures):
    response = client.patch("/api/v2/admin/configs/EVENT_NAME", headers={"X-ADCE-SECRET": "test"}, json={"value": "Test Contest"})
    assert response.status_code == 200
    assert get_config("EVENT_NAME") == "Test Contest"

    response = client.patch("/api/v2/admin/configs/TICK_DURATION", headers={"X-ADCE-SECRET": "test"}, json={"value": 5})
    assert response.status_code == 200
    assert get_config("TICK_DURATION") == 5

    response = client.patch(
        "/api/v2/admin/configs/CORS_WHITELIST",
        headers={"X-ADCE-SECRET": "test", "Origin": "https://random.random"},
        json={"value": ["https://random.random"]}
    )
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "https://random.random"
    
    response = client.get("/api/v2/admin/configs/", headers={"X-ADCE-SECRET": "test", "Origin": "https://other.other"})
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == None

def test_fail_patch_configs(client: FlaskClient, config_fixtures):
    response = client.patch("/api/v2/admin/configs/NONEXIST_KEY", headers={"X-ADCE-SECRET": "test"}, json={"value": "Test Contest"})
    assert response.status_code == 404
    assert response.get_json()['message'] == "configuration key not found."

    response = client.patch("/api/v2/admin/configs/EVENT_NAME", headers={"X-ADCE-SECRET": "test"}, json={"key": "Test Contest"})
    assert response.status_code == 400
    assert response.get_json()['message'] == "missing 'value' key in body request."