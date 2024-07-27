from ailurus.models import db, Team, Challenge, Service, CheckerResult, ChallengeRelease, CheckerStatus
from ailurus.utils.config import set_config
from flask.testing import FlaskClient
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
        Service(team_id=1, challenge_id=1, order=1, secret="test", detail=json.dumps({"test":"value"})),
        Service(team_id=1, challenge_id=1, order=2, secret="test", detail=json.dumps({"test":"value"})),
        Service(team_id=1, challenge_id=2, order=1, secret="test", detail=json.dumps({"test":"value"})),
        Service(team_id=2, challenge_id=2, order=1, secret="test", detail=json.dumps({"test":"value"})),
    ]
    db.session.add_all(teams + challenges + chall_releases + services)
    db.session.commit()

def test_get_all_service_status_correct(client: FlaskClient, service_status):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/services-status")
    assert response.status_code == 200
    assert response.get_json()["data"] == {}

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/services-status")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["1"] == {"1": {"detail": {"test": "3"}, "status": 0}}
    assert response_data["2"] == {"2": {"status": 1, "detail": {"test": "7"}}, "1": {"status": 0, "detail": {"test": "6"}}}
    assert len(response_data.keys()) == 2

def test_get_service_status_by_teamid_correct(client: FlaskClient, service_status):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/teams/999/services-status")
    assert response.status_code == 404

    response = client.get("/api/v2/teams/1/services-status")
    assert response.status_code == 200
    assert response.get_json()["data"] == {}

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/teams/1/services-status")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["1"] == {"detail": {"test": "3"}, "status": 0}
    assert response_data["2"] == {"status": 0, "detail": {"test": "6"}}
    assert len(response_data.keys()) == 2


def test_get_service_status_by_challid_correct(client: FlaskClient, service_status):
    set_config("SERVICE_MODE", "sample")

    response = client.get("/api/v2/challenges/999/services-status")
    assert response.status_code == 404

    response = client.get("/api/v2/challenges/1/services-status")
    assert response.status_code == 404

    set_config("CURRENT_ROUND", "1")
    response = client.get("/api/v2/challenges/1/services-status")
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["1"] == {"detail": {"test": "3"}, "status": 0}
    assert len(response_data.keys()) == 1