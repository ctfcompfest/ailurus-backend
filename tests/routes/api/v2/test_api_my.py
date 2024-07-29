from ailurus.models import db, Solve, ChallengeRelease, Team, Challenge, CheckerResult, CheckerStatus
from ailurus.utils.config import set_config
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token
import pytest
import json

@pytest.fixture
def chall_data():
    teams = [
        Team(name="team 1", email="team1@mail.com", password="test"),
        Team(name="team 2", email="team2@mail.com", password="test"),
    ]
    challenges = [
        Challenge(slug=f"chall1", title=f"Chall 1", description="desc"),
        Challenge(slug=f"chall2", title=f"Chall 2", description="desc", testcase_checksum="test"),
        Challenge(slug=f"chall3", title=f"Chall 3", description="desc"),
    ]
    chall_releases = [
        ChallengeRelease(round=1, challenge_id=1),
        ChallengeRelease(round=1, challenge_id=2),
    ]
    db.session.add_all(teams + challenges + chall_releases)
    db.session.commit()

@pytest.fixture
def service_status(chall_data):
    checker_results = [
        CheckerResult(team_id=1, challenge_id=1, round=1, tick=1, status=CheckerStatus(0), detail=json.dumps({"test":"1"})),
        CheckerResult(team_id=1, challenge_id=1, round=1, tick=1, status=CheckerStatus(0), detail=json.dumps({"test":"2"})),
        CheckerResult(team_id=1, challenge_id=1, round=1, tick=1, status=CheckerStatus(0), detail=json.dumps({"test":"3"})),
        CheckerResult(team_id=1, challenge_id=1, round=1, tick=1, status=CheckerStatus(99), detail=json.dumps({"test":"4"})),
        
        CheckerResult(team_id=1, challenge_id=2, round=1, tick=1, status=CheckerStatus(0), detail=json.dumps({"test":"5"})),
        CheckerResult(team_id=1, challenge_id=2, round=1, tick=1, status=CheckerStatus(0), detail=json.dumps({"test":"6"})),
        
        CheckerResult(team_id=2, challenge_id=2, round=1, tick=1, status=CheckerStatus(1), detail=json.dumps({"test":"7"})),
        CheckerResult(team_id=2, challenge_id=2, round=1, tick=1, status=CheckerStatus(99), detail=json.dumps({"test":"8"})),
        
        CheckerResult(team_id=2, challenge_id=3, round=1, tick=1, status=CheckerStatus(-1), detail=json.dumps({"test":"9"})),
        CheckerResult(team_id=2, challenge_id=3, round=1, tick=1, status=CheckerStatus(0), detail=json.dumps({"test":"10"})),
    ]
    db.session.add_all(checker_results)
    db.session.commit()


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

def test_get_allow_manage_services_success(client: FlaskClient, solves_data):
    access_token = create_access_token(identity={"team":{"id": 1}})

    set_config("UNLOCK_MODE", "solvefirst")
    resp = client.get("/api/v2/my/allow-manage-services/", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.get_json()["data"] == [1]

    set_config("UNLOCK_MODE", "nolock")
    resp = client.get("/api/v2/my/allow-manage-services/", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.get_json()["data"] == [1, 3]

def test_unauthorized_get_my(client: FlaskClient):
    resp = client.get("/api/v2/my/solves/")
    assert resp.status_code == 401

    resp = client.get("/api/v2/my/allow-manage-services/")
    assert resp.status_code == 401

def test_get_my_solves(client: FlaskClient, solves_data):
    access_token = create_access_token(identity={"team":{"id": 1}})
    resp = client.get("/api/v2/my/solves/", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.get_json()["data"] == [1]

def test_handle_service_manager(client: FlaskClient, solves_data):
    set_config("SERVICE_MODE", "sample")
    access_token = create_access_token(identity={"team":{"id": 1}})
    
    resp = client.post("/api/v2/my/challenges/1/service-manager/", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.get_json()['message'] == "success"

    resp = client.post("/api/v2/my/challenges/2/service-manager/", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 404

    resp = client.post("/api/v2/my/challenges/3/service-manager/", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 403
    assert resp.get_json()['message'] == "failed"

    set_config("UNLOCK_MODE", "nolock")
    resp = client.post("/api/v2/my/challenges/3/service-manager/", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.get_json()['message'] == "success"


def test_get_service_status_by_teamid_and_challid_correct(client: FlaskClient, service_status):
    set_config("SERVICE_MODE", "sample")
    access_token = create_access_token(identity={"team":{"id": 1}})

    response = client.get("/api/v2/my/challenges/999/services-status/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 404

    response = client.get("/api/v2/my/challenges/1/services-status/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 404

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/my/challenges/1/services-status/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"detail": {"test": "3"}, "status": 0}

    response = client.get("/api/v2/my/challenges/2/services-status/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"status": 0, "detail": {"test": "6"}}


def test_get_service_status_when_checkerresult_empty(client: FlaskClient, chall_data):
    set_config("SERVICE_MODE", "sample")
    set_config("CURRENT_ROUND", "1")
    access_token = create_access_token(identity={"team":{"id": 1}})

    response = client.get("/api/v2/my/challenges/1/services-status/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"status": 1, "detail": {}}
