from ailurus.models import db, Challenge, Team, CheckerResult
from flask.testing import FlaskClient
from flask import current_app
from typing import List
import io
import os
import pytest
import zipfile
import json

def create_zip_file(file_name, file_content):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(file_name, file_content)
    zip_buffer.seek(0)
    return zip_buffer

@pytest.fixture
def challenge_fixture():
    challenges = [
        Challenge(slug=f"chall1", title=f"Chall 1", description="desc"),
        Challenge(slug=f"chall2", title=f"Chall 2", description="desc"),
    ]
    db.session.add_all(challenges)
    db.session.commit()
    return challenges

@pytest.fixture
def team_fixture():
    teams = [
        Team(name="team 1", email="team1@mail.com", password="test"),
        Team(name="team 2", email="team2@mail.com", password="test"),
    ]
    db.session.add_all(teams)
    db.session.commit()
    return teams

def test_get_testcase_challenge(client: FlaskClient, challenge_fixture):
    zip_buffer = create_zip_file('test.txt', b'testing')
    response = client.post(
        "/api/v2/admin/challenges/1/testcase/",
        headers={"X-ADMIN-SECRET": "test"},
        data={
            "testcase": (zip_buffer, "test.zip")
        }
    )
    assert response.status_code == 200

    response = client.get(
        "/api/v2/worker/testcase/1/",
        headers={"X-WORKER-SECRET": "test"},
    )
    assert response.status_code == 200
    assert zipfile.is_zipfile(io.BytesIO(response.data))

def test_fail_get_testcase_challenge(client: FlaskClient, challenge_fixture):
    response = client.get(
        "/api/v2/worker/testcase/1/",
        headers={"X-WORKER-SECRET": "test"},
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "testcase not found."

    response = client.get(
        "/api/v2/worker/testcase/999/",
        headers={"X-WORKER-SECRET": "test"},
    )
    assert response.status_code == 404
    assert response.get_json()["message"] == "challenge not found."

def test_get_artifact_challenge(client: FlaskClient, challenge_fixture):
    zip_buffer = create_zip_file('test.txt', b'testing')
    response = client.post(
        "/api/v2/admin/challenges/1/artifact/",
        headers={"X-ADMIN-SECRET": "test"},
        data={
            "artifact": (zip_buffer, "test.zip")
        }
    )
    assert response.status_code == 200

    response = client.get(
        "/api/v2/worker/artifact/1/",
        headers={"X-WORKER-SECRET": "test"},
    )
    assert response.status_code == 200
    assert zipfile.is_zipfile(io.BytesIO(response.data))

def test_fail_get_artifact_challenge(client: FlaskClient, challenge_fixture):
    response = client.get(
        "/api/v2/worker/artifact/1/",
        headers={"X-WORKER-SECRET": "test"},
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "artifact not found."

    response = client.get(
        "/api/v2/worker/artifact/999/",
        headers={"X-WORKER-SECRET": "test"},
    )
    assert response.status_code == 404
    assert response.get_json()["message"] == "challenge not found."

def test_invalid_field_submit_checker_result(client: FlaskClient, challenge_fixture, team_fixture):
    response = client.post(
        "/api/v2/worker/checkresults/",
        headers={"X-WORKER-SECRET": "test"},
        json={
            "team_id": 100,
            "challenge_id": 1,
            "round": 1,
            "status": 0,
            "detail": {"status": "test"}
        }
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "missing required value."
    assert CheckerResult.query.count() == 0

    response = client.post(
        "/api/v2/worker/checkresults/",
        headers={"X-WORKER-SECRET": "test"},
        json={
            "team_id": 100,
            "challenge_id": 1,
            "round": 1,
            "tick": 1,
            "status": 0,
            "detail": {"status": "test"}
        }
    )
    assert response.status_code == 400
    assert CheckerResult.query.count() == 0
    assert response.get_json()["message"] == "team not found."

    response = client.post(
        "/api/v2/worker/checkresults/",
        headers={"X-WORKER-SECRET": "test"},
        json={
            "team_id": 1,
            "challenge_id": 100,
            "round": 1,
            "tick": 1,
            "status": 0,
            "detail": {"status": "test"}
        }
    )
    assert response.status_code == 400
    assert CheckerResult.query.count() == 0
    assert response.get_json()["message"] == "challenge not found."


def test_submit_checker_result(client: FlaskClient, challenge_fixture, team_fixture):
    response = client.post(
        "/api/v2/worker/checkresults/",
        headers={"X-WORKER-SECRET": "test"},
        json={
            "team_id": 1,
            "challenge_id": 1,
            "round": 1,
            "tick": 1,
            "status": 0,
            "detail": {"status": "test"}
        }
    )
    assert response.status_code == 200
    assert CheckerResult.query.count() == 1