from ailurus.models import db, Solve, ChallengeRelease, Team
from ailurus.utils.config import set_config
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token
import pytest

@pytest.fixture
def solves_data():
    team = Team(name="team 1", email="mail@mail.com", password="test")
    solves = [
        Solve(team_id=1, challenge_id=1),
        Solve(team_id=2, challenge_id=1),
        Solve(team_id=1, challenge_id=2),
    ]
    chall_releases = [
        ChallengeRelease(round=1, challenge_id=1),
        ChallengeRelease(round=1, challenge_id=3),
    ]
    db.session.add(team)
    db.session.add_all(solves + chall_releases)
    db.session.commit()
    set_config("CURRENT_ROUND", "1")

def test_unauthorized_get_my_solves(client: FlaskClient):
    resp = client.get("/api/v2/my/solves")
    assert resp.status_code == 401

def test_get_my_solves(client: FlaskClient, solves_data):
    access_token = create_access_token(identity={"team":{"id": 1}})
    resp = client.get("/api/v2/my/solves", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.get_json()["data"] == [1]

def test_handle_service_manager(client: FlaskClient, solves_data):
    set_config("SERVICE_MODE", "sample")
    access_token = create_access_token(identity={"team":{"id": 1}})
    
    resp = client.post("/api/v2/my/challenges/1/service-manager", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.get_json()['message'] == "success"

    resp = client.post("/api/v2/my/challenges/2/service-manager", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 404

    resp = client.post("/api/v2/my/challenges/3/service-manager", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 403
    assert resp.get_json()['message'] == "failed"