from ailurus.models import db, Team, Challenge, ChallengeRelease, Flag, Solve, Submission
from ailurus.utils.config import set_config
from ailurus.utils.config import (
    is_contest_started,
    is_contest_paused,
    is_contest_finished,
    is_contest_running,
)
from datetime import datetime, timezone, timedelta
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token

import pytest

@pytest.fixture
def data_fixture():
    set_config("IS_CONTEST_PAUSED", "false")
    set_config("NUMBER_ROUND", "3")
    set_config("CURRENT_ROUND", "1")
    set_config("CURRENT_TICK", "2")
    teams = [
        Team(name=f"team{i}", email=f"mail{i}@mail.com", password="test")
        for i in range(2)
    ]
    challs = [
        Challenge(slug=f"chall{i}", title="title", description="desc")
        for i in range(2)
    ]
    db.session.add_all(teams + challs)
    db.session.add(ChallengeRelease(round=1, challenge_id=1))
    db.session.commit()

    flags = []
    for tick in range(1, 3):
        for team in teams:
            for chall in challs:
                flags.append(Flag(
                    team_id=team.id,
                    challenge_id=chall.id,
                    round=1,
                    tick=tick,
                    value=f"flag{chall.id}{team.id}{tick}",
                ))
    db.session.add_all(flags)
    db.session.commit()

@pytest.fixture
def request_headers():
    access_token = create_access_token(identity={"team": {"id": 1}})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def contest_started():
    start_time = datetime.now(timezone.utc) - timedelta(days=1)
    set_config("START_TIME", start_time.isoformat())

def test_submit_when_notstarted(client: FlaskClient, request_headers, data_fixture):
    set_config("START_TIME", "3000-01-01T01:00:00+00:00")

    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag"]})
    assert not is_contest_started()
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "contest is not running."
    assert Submission.query.count() == 0

def test_submit_when_paused(client: FlaskClient, request_headers, contest_started, data_fixture):
    set_config("IS_CONTEST_PAUSED", "true")
    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag"]})
    assert is_contest_started() and is_contest_paused() and not is_contest_finished()
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "contest is not running."
    assert Submission.query.count() == 0

def test_submit_when_finished(client: FlaskClient, request_headers, contest_started, data_fixture):
    set_config("CURRENT_ROUND", "4")
    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag"]})
    assert is_contest_finished()
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "contest is not running."
    assert Submission.query.count() == 0

def test_submit_missing_field(client: FlaskClient, request_headers, data_fixture, contest_started):
    assert is_contest_running()
    resp = client.post("/api/v2/submit/", headers=request_headers, json={"wrong": "test"})
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "missing 'flags' field."
    assert Submission.query.count() == 0
    
def test_submit_max_bulk(client: FlaskClient, request_headers, data_fixture, contest_started):
    set_config("MAX_BULK_SUBMIT", "3")
    assert is_contest_running()
    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag112","flag122","flag122","flag122"]})
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "maximum 3 flags at a time."
    assert Submission.query.count() == 0

def test_submit_expired_flag(client: FlaskClient, request_headers, data_fixture, contest_started):
    assert is_contest_running()
    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag111", "flag121"]})
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag is wrong or expired."
    assert Submission.query.count() == 2
    assert Solve.query.count() == 0

def test_submit_wrong_flag(client: FlaskClient, request_headers, data_fixture, contest_started):
    assert is_contest_running()
    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flagtest"]})
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag is wrong or expired."
    assert Submission.query.count() == 1
    assert Solve.query.count() == 0

def test_submit_hidden_flag(client: FlaskClient, request_headers, data_fixture, contest_started):
    assert is_contest_running()
    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag212","flag212"]})
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag is wrong or expired."
    assert Submission.query.count() == 2
    assert Solve.query.count() == 0

def test_submit_correct_flags_as_solvefirst(client: FlaskClient, request_headers, data_fixture, contest_started):
    set_config("UNLOCK_MODE", "solvefirst")

    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag122"]})
    assert is_contest_running()
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag is correct."
    assert Submission.query.count() == 1
    assert Solve.query.count() == 0

    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag112"]})
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag is correct."
    assert Submission.query.count() == 2
    assert Solve.query.count() == 1


def test_submit_correct_flags_as_nolock(client: FlaskClient, request_headers, data_fixture, contest_started):
    set_config("UNLOCK_MODE", "nolock")

    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag122"]})
    assert is_contest_running()
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag is correct."
    assert Submission.query.count() == 1
    assert Solve.query.count() == 1

    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag112"]})
    assert is_contest_running()
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag is correct."
    assert Submission.query.count() == 2
    assert Solve.query.count() == 1

def test_double_submit_correct_flags(client: FlaskClient, request_headers, data_fixture, contest_started):
    set_config("UNLOCK_MODE", "nolock")
    assert is_contest_running()

    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag122"]})
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag is correct."
    assert Submission.query.count() == 1
    assert Solve.query.count() == 1

    resp = client.post("/api/v2/submit/", headers=request_headers, json={"flags": ["flag122"]})
    assert resp.status_code == 200
    resp_data = resp.get_json()["data"]
    for result in resp_data:
        assert result['verdict'] == "flag already submitted."
    assert Submission.query.count() == 1
    assert Solve.query.count() == 1
