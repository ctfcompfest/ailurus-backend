from ailurus.models import db, Team, Challenge, Service, CheckerResult, ChallengeRelease, CheckerStatus
from ailurus.utils.config import set_config
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token
import pytest
import json

@pytest.fixture
def service_status():
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
    db.session.add_all(teams + challenges + chall_releases + checker_results)
    db.session.commit()

@pytest.fixture
def services_data():
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
    services = [
        Service(team_id=1, challenge_id=1, order=1, secret="test", detail=json.dumps({"test":"1"})),
        Service(team_id=1, challenge_id=1, order=2, secret="test", detail=json.dumps({"test":"2"})),
        Service(team_id=1, challenge_id=2, order=1, secret="test", detail=json.dumps({"test":"3"})),
        Service(team_id=2, challenge_id=2, order=1, secret="test", detail=json.dumps({"test":"4"})),
    ]
    db.session.add_all(teams + challenges + chall_releases + services)
    db.session.commit()

@pytest.fixture
def auth_headers(webapp: Flask):
    acc_token = create_access_token(identity={"team": {"id": 1}})
    return {"Authorization": f"Bearer {acc_token}"}

def test_get_all_service_status_correct(client: FlaskClient, service_status):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/services-status/")
    assert response.status_code == 200
    assert response.get_json()["data"] == {}

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/services-status/")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["1"] == {"1": {"detail": {"test": "3"}, "status": 0}}
    assert response_data["2"] == {"2": {"status": 1, "detail": {"test": "7"}}, "1": {"status": 0, "detail": {"test": "6"}}}
    assert len(response_data.keys()) == 2


def test_get_service_status_when_db_empty(client: FlaskClient):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/services-status/")
    assert response.status_code == 200
    assert response.get_json()["data"] == {}

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/services-status/")
    assert response.status_code == 200
    assert response.get_json()["data"] == {}


def test_get_service_status_by_teamid_correct(client: FlaskClient, service_status):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/teams/999/services-status/")
    assert response.status_code == 404

    response = client.get("/api/v2/teams/1/services-status/")
    assert response.status_code == 200
    assert response.get_json()["data"] == {}

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/teams/1/services-status/")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["1"] == {"detail": {"test": "3"}, "status": 0}
    assert response_data["2"] == {"status": 0, "detail": {"test": "6"}}
    assert len(response_data.keys()) == 2

def test_get_service_status_by_teamid_and_challid_correct(client: FlaskClient, service_status):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/teams/999/challenges/1/services-status/")
    assert response.status_code == 404

    response = client.get("/api/v2/teams/1/challenges/999/services-status/")
    assert response.status_code == 404

    response = client.get("/api/v2/teams/1/challenges/1/services-status/")
    assert response.status_code == 404

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/teams/1/challenges/1/services-status/")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"detail": {"test": "3"}, "status": 0}

    response = client.get("/api/v2/teams/1/challenges/2/services-status/")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"status": 0, "detail": {"test": "6"}}

def test_get_service_status_by_challid_correct(client: FlaskClient, service_status):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/challenges/999/services-status/")
    assert response.status_code == 404

    response = client.get("/api/v2/challenges/1/services-status/")
    assert response.status_code == 404

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/challenges/1/services-status/")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"1": {"detail": {"test": "3"}, "status": 0}}
    assert len(response_data.keys()) == 1

    response = client.get("/api/v2/challenges/2/services-status/")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"2": {"status": 1, "detail": {"test": "7"}}, "1": {"status": 0, "detail": {"test": "6"}}}
    assert len(response_data.keys()) == 2

def test_get_all_service_correct(client: FlaskClient, services_data, auth_headers):
    set_config("SERVICE_MODE", "sample")
    
    response = client.get("/api/v2/services/")
    assert response.status_code == 401
    
    response = client.get("/api/v2/services/", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["data"] == {}

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["1"] == {"1": [{"test": "1"}, {"test": "2"}], "2": []}
    assert response_data["2"] == {"1": [{"test": "3"}], "2": [{"test": "4"}]}
    assert len(response_data.keys()) == 2

def test_get_service_from_challid(client: FlaskClient, services_data, auth_headers):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/challenges/1/services/")
    assert response.status_code == 401

    response = client.get("/api/v2/challenges/1/services/", headers=auth_headers)
    assert response.status_code == 404

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/challenges/1/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"1": [{"test": "1"}, {"test": "2"}], "2": []}

    response = client.get("/api/v2/challenges/2/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"1": [{"test": "3"}], "2": [{"test": "4"}]}


def test_get_service_from_teamid(client: FlaskClient, services_data, auth_headers):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/teams/999/services/")
    assert response.status_code == 401

    response = client.get("/api/v2/teams/999/services/", headers=auth_headers)
    assert response.status_code == 404

    response = client.get("/api/v2/teams/1/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {}

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/teams/1/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"1": [{"test": "1"}, {"test": "2"}], "2": [{"test": "3"}]}

    response = client.get("/api/v2/teams/2/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == {"1": [], "2": [{"test": "4"}]}

def test_get_service_from_teamid_and_challid(client: FlaskClient, services_data, auth_headers):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/teams/1/challenges/1/services/")
    assert response.status_code == 401

    response = client.get("/api/v2/teams/999/challenges/1/services/", headers=auth_headers)
    assert response.status_code == 404

    response = client.get("/api/v2/teams/1/challenges/999/services/", headers=auth_headers)
    assert response.status_code == 404

    response = client.get("/api/v2/teams/1/challenges/1/services/", headers=auth_headers)
    assert response.status_code == 404

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/teams/1/challenges/1/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == [{"test": "1"}, {"test": "2"}]

    response = client.get("/api/v2/teams/1/challenges/2/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == [{"test": "3"}]

    response = client.get("/api/v2/teams/2/challenges/1/services/", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data == []