from base64 import b64decode
from datetime import timedelta
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token
import json
import pytest

@pytest.fixture
def team_account(client: FlaskClient):
    team_data = [
        {'name': 'John Doe', 'email': 'team1@example.com', 'password': 'myPass1234'},
        {'name': 'John Die', 'email': 'team2@example.com', 'password': 'myPass1234'}
    ]
    client.post('/api/v2/admin/teams/', headers={"X-ADMIN-SECRET": "test"}, json=team_data)
    return team_data

def test_success_auth(client: FlaskClient, team_account):
    response = client.post("/api/v2/authenticate/", json={"email": "team1@example.com", "password": "myPass1234"})
    assert response.status_code == 200
    
    claim_jwt = response.get_json()["data"].split(".")[1]
    claim_jwt += "=" * (4 - (len(claim_jwt) % 4))
    claim = json.loads(b64decode(claim_jwt.encode()))
    assert claim["sub"]["team"]["id"] == 1
    assert claim["sub"]["team"]["name"] == "John Doe"

def test_fail_auth(client: FlaskClient, team_account):
    response = client.post("/api/v2/authenticate/", json={"email": "fake@example.com", "password": "myPass1234"})
    assert response.status_code == 403
    assert response.get_json()["message"] == "email or password is wrong."
    
    response = client.post("/api/v2/authenticate/", json={"email": "team2@example.com", "password": "wrongPass"})
    assert response.status_code == 403
    assert response.get_json()["message"] == "email or password is wrong."
    
    response = client.post("/api/v2/authenticate/", json={"password": "myPass1234"})
    assert response.status_code == 403
    assert response.get_json()["message"] == "email or password is wrong."
    
    response = client.post("/api/v2/authenticate/", json={"email": "team2@example.com"})
    assert response.status_code == 403
    assert response.get_json()["message"] == "email or password is wrong."
    

def test_token_check(client: FlaskClient, team_account):
    team_jwt = create_access_token(
        identity={"team": {"id": 1, "name": team_account[0]["name"]}}
    )
    response = client.post("/api/v2/authenticate/token-check/", headers={
        "Authorization": f"Bearer {team_jwt}",
    })
    assert response.status_code == 200
    assert response.get_json()["message"] == "token is valid."

def test_fail_token_check(client: FlaskClient, team_account):
    expired_token = create_access_token(
        identity={"team": {"id": 1, "name": team_account[0]["name"]}},
        expires_delta=timedelta(days=-10)
    )
    response = client.post("/api/v2/authenticate/token-check/", headers={
        "Authorization": f"Bearer {expired_token}",
    })
    assert response.status_code == 401

    nonexist_team_token = create_access_token(
        identity={"team": {"id": 999, "name": "Invalid Team"}}
    )
    response = client.post("/api/v2/authenticate/token-check/", headers={
        "Authorization": f"Bearer {nonexist_team_token}",
    })
    assert response.status_code == 401
