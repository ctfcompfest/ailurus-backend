from ailurus.models import db, Challenge, ChallengeRelease
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
def data_fixtures() -> List[Challenge]:
    challenges = [
        Challenge(slug=f"chall1", title=f"Chall 1", description="desc"),
        Challenge(slug=f"chall2", title=f"Chall 2", description="desc", testcase_checksum="test"),
        Challenge(slug=f"chall3", title=f"Chall 3", description="desc"),
    ]
    db.session.add_all(challenges)
    db.session.commit()

    chall_releases = [
        ChallengeRelease(round=1, challenge_id=1),
        ChallengeRelease(round=2, challenge_id=1),
        ChallengeRelease(round=3, challenge_id=1),
        ChallengeRelease(round=1, challenge_id=2),
        ChallengeRelease(round=2, challenge_id=2),
    ]
    db.session.add_all(chall_releases)
    db.session.commit() 
    return challenges

def test_get_all_challenges(client: FlaskClient, data_fixtures: List[Challenge]):
    response = client.get("/api/v2/admin/challenges/", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert len(response_data) == len(data_fixtures)

def test_get_challenge_detail(client: FlaskClient, data_fixtures: List[Challenge]):
    response = client.get("/api/v2/admin/challenges/1", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["slug"] == "chall1"
    assert response_data["testcase_checksum"] == None
    assert response_data["visibility"] == [1, 2, 3]

    response = client.get("/api/v2/admin/challenges/2", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["slug"] == "chall2"
    assert response_data["testcase_checksum"] == "test"
    assert response_data["visibility"] == [1, 2]

    response = client.get("/api/v2/admin/challenges/3", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["slug"] == "chall3"
    assert response_data["testcase_checksum"] == None
    assert response_data["visibility"] == []

    response = client.get("/api/v2/admin/challenges/9999", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 404
    assert response.get_json()["message"] == "challenge not found."

def test_patch_challenge_detail(client: FlaskClient, data_fixtures: List[Challenge]):
    response = client.patch(
        "/api/v2/admin/challenges/1",
        headers={"X-ADCE-SECRET": "test"},
        json={"testcase_checksum": "hahaha", "slug": "challxx", "artifact_checksum": "yoyoyo"}
    )
    assert response.status_code == 200
    response_data = response.get_json()["data"]
    assert response_data["slug"] == "challxx"
    assert response_data["testcase_checksum"] == None
    assert response_data["artifact_checksum"] == None
    assert response_data["visibility"] == [1, 2, 3]

    response = client.patch(
        "/api/v2/admin/challenges/1",
        headers={"X-ADCE-SECRET": "test"},
        json={"visibility": [4, 6]}
    )
    assert response.status_code == 200
    assert ChallengeRelease.get_rounds_from_challenge(1) == [4, 6]

    response = client.patch(
        "/api/v2/admin/challenges/1",
        headers={"X-ADCE-SECRET": "test"},
        json={"visibility": []}
    )
    assert response.status_code == 200
    assert ChallengeRelease.get_rounds_from_challenge(1) == []

def test_fail_patch_challenge_detail(client: FlaskClient, data_fixtures: List[Challenge]):
    response = client.patch(
        "/api/v2/admin/challenges/1",
        headers={"X-ADCE-SECRET": "test"},
        json={"slug": "chall2", "visibility": [1, 2, 3, 4, 5]}
    )
    assert response.status_code == 400
    assert response.get_json()['message'] == "your update conflict with current data."
    assert ChallengeRelease.get_rounds_from_challenge(1) == [1, 2, 3]

    response = client.patch(
        "/api/v2/admin/challenges/999",
        headers={"X-ADCE-SECRET": "test"},
        json={"testcase_checksum": "hahaha"}
    )
    assert response.status_code == 404
    assert response.get_json()['message'] == "challenge not found."

def test_post_testcase(client: FlaskClient, data_fixtures: List[Challenge]):
    zip_buffer = create_zip_file('test.txt', b'testing')
    response = client.post(
        "/api/v2/admin/challenges/1/testcase",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "testcase": (zip_buffer, "test.zip")
        }
    )
    assert response.status_code == 200
    chall: Challenge = Challenge.query.filter_by(id=1).first()
    assert chall.testcase_checksum != None
    fileuploaded = os.path.join(current_app.config["DATA_DIR"], "challenges", "testcase-1.zip")
    assert zipfile.is_zipfile(fileuploaded)
    os.remove(fileuploaded)

def test_fail_post_testcase(client: FlaskClient, data_fixtures: List[Challenge]):
    response = client.post(
        "/api/v2/admin/challenges/999/testcase",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "testcase": (io.BytesIO(b"a"), "test.zip")
        }
    )
    assert response.status_code == 404
    assert response.get_json()["message"] == "challenge not found."

    response = client.post(
        "/api/v2/admin/challenges/1/testcase",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "testcase": (io.BytesIO(b"a"), "test.zip")
        }
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "invalid testcase zip file."
    
    response = client.post(
        "/api/v2/admin/challenges/1/testcase",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "file": (io.BytesIO(b"a"), "test.zip")
        }
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "missing 'testcase' field."


def test_post_artifact(client: FlaskClient, data_fixtures: List[Challenge]):
    zip_buffer = create_zip_file('pop.txt', b'file test')
    response = client.post(
        "/api/v2/admin/challenges/1/artifact",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "artifact": (zip_buffer, "test.zip")
        }
    )
    assert response.status_code == 200
    chall: Challenge = Challenge.query.filter_by(id=1).first()
    assert chall.artifact_checksum != None
    fileuploaded = os.path.join(current_app.config["DATA_DIR"], "challenges", "artifact-1.zip")
    assert zipfile.is_zipfile(fileuploaded)
    os.remove(fileuploaded)


def test_fail_post_artifact(client: FlaskClient, data_fixtures: List[Challenge]):
    response = client.post(
        "/api/v2/admin/challenges/999/artifact",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "artifact": (io.BytesIO(b"a"), "test.zip")
        }
    )
    assert response.status_code == 404
    assert response.get_json()["message"] == "challenge not found."

    response = client.post(
        "/api/v2/admin/challenges/1/artifact",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "artifact": (io.BytesIO(b"a"), "test.zip")
        }
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "invalid artifact zip file."
    
    response = client.post(
        "/api/v2/admin/challenges/1/artifact",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "file": (io.BytesIO(b"a"), "test.zip")
        }
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "missing 'artifact' field."

def test_create_bulk_challs(client: FlaskClient):
    data = [
        {"slug": "chall1", "title": "Chall 1", "description": "desc", "point": 1, "num_service": 1, "num_flag": 1, "visibility": [1, 2]},
        {"slug": "chall2", "title": "Chall 2", "description": "desc", "point": 1, "num_service": 1, "num_flag": 1},
        {"slug": "chall3", "title": "Chall 3", "description": "desc", "point": 1, "num_service": 1, "num_flag": 1},
        {"slug": "chall4", "title": "Chall 3", "description": "desc", "point": 1, "num_service": 1, "num_flag": 1},
    ]
    response = client.post(
        "/api/v2/admin/challenges/",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "data": json.dumps(data),
            "testcase[0]": (create_zip_file('pop.txt', b'file test'), "test.zip"),
            "artifact[0]": (create_zip_file('pop.txt', b'file test'), "test.zip"),
            "testcase[1]": (create_zip_file('pop.txt', b'file test'), "test.zip"),
            "artifact[2]": (create_zip_file('pop.txt', b'file test'), "test.zip"),
        }
    )
    assert response.status_code == 200

    chall1: Challenge = Challenge.query.filter_by(id=1).first()
    assert chall1.slug == "chall1"
    assert chall1.artifact_checksum != None
    assert chall1.testcase_checksum != None
    assert ChallengeRelease.get_rounds_from_challenge(1) == [1, 2]

    chall2: Challenge = Challenge.query.filter_by(id=2).first()
    assert chall2.slug == "chall2"
    assert chall2.artifact_checksum == None
    assert chall2.testcase_checksum != None
    assert ChallengeRelease.get_rounds_from_challenge(2) == []

    chall3: Challenge = Challenge.query.filter_by(id=3).first()
    assert chall3.slug == "chall3"
    assert chall3.artifact_checksum != None
    assert chall3.testcase_checksum == None
    assert ChallengeRelease.get_rounds_from_challenge(3) == []

    chall4: Challenge = Challenge.query.filter_by(id=4).first()
    assert chall4.slug == "chall4"
    assert chall4.artifact_checksum == None
    assert chall4.testcase_checksum == None
    assert ChallengeRelease.get_rounds_from_challenge(4) == []

def test_fail_create_bulk_challs(client: FlaskClient, data_fixtures: List[Challenge]):
    data = {"slug": "chall1", "title": "Chall 1", "description": "desc", "point": 1, "num_service": 1, "num_flag": 1, "visibility": [1, 2]}
    response = client.post(
        "/api/v2/admin/challenges/",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "data": json.dumps([data]),
        }
    )
    assert response.status_code == 400

    response = client.post(
        "/api/v2/admin/challenges/",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "data": json.dumps([data, data]),
        }
    )
    assert response.status_code == 400


    incomplete_data = {"slug": "chall1", "description": "desc", "point": 1, "num_service": 1, "num_flag": 1, "visibility": [1, 2]} 
    response = client.post(
        "/api/v2/admin/challenges/",
        headers={"X-ADCE-SECRET": "test"},
        data={
            "data": json.dumps([incomplete_data]),
        }
    )
    assert response.status_code == 400

    response = client.post(
        "/api/v2/admin/challenges/",
        headers={"X-ADCE-SECRET": "test"},
    )
    assert response.status_code == 400
