from ailurus.models import db, Team
from flask.testing import FlaskClient
from base64 import b64decode
import json

def test_success_auth(client: FlaskClient):
    team_data = [
        {'name': 'John Doe', 'email': 'team1@example.com', 'password': 'myPass1234'},
        {'name': 'John Die', 'email': 'team2@example.com', 'password': 'myPass1234'}
    ]
    response = client.post('/api/v2/admin/teams/', headers={"X-ADCE-SECRET": "test"}, json=team_data)

    response = client.post("/api/v2/authenticate/", json={"email": "team1@example.com", "password": "myPass1234"})
    assert response.status_code == 200
    
    claim_jwt = response.get_json()["data"].split(".")[1]
    claim_jwt += "=" * (4 - (len(claim_jwt) % 4))
    claim = json.loads(b64decode(claim_jwt.encode()))
    assert claim["sub"]["team"]["id"] == 1
    assert claim["sub"]["team"]["name"] == "John Doe"

def test_fail_auth(client: FlaskClient):
    team_data = [
        {'name': 'John Doe', 'email': 'team1@example.com', 'password': 'myPass1234'},
        {'name': 'John Die', 'email': 'team2@example.com', 'password': 'myPass1234'}
    ]
    response = client.post('/api/v2/admin/teams/', headers={"X-ADCE-SECRET": "test"}, json=team_data)

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
    
