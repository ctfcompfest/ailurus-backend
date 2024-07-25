from ailurus.models import db, Challenge, ChallengeRelease, Team
from ailurus.utils.config import set_config
from datetime import timedelta
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token
from typing import List

import pytest

@pytest.fixture
def data_fixture() -> List[Challenge]:
    db.session.add(Team(id=1, name="team 1", email="mail@mail.com", password="test"))
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

def test_get_all_challenges(client: FlaskClient, data_fixture: List[Challenge]):
    set_config("CURRENT_ROUND", 1)
    response = client.get("/api/v2/challenges/")
    assert response.status_code == 200

    datas = response.get_json()['data']
    assert len(datas) == 2
    for data in datas:
        assert data["id"] in [1, 2]

    set_config("CURRENT_ROUND", 3)
    response = client.get("/api/v2/challenges/")
    assert response.status_code == 200

    datas = response.get_json()['data']
    assert len(datas) == 1
    for data in datas:
        assert data["id"] in [1]


def test_public_get_detail_challenge(client: FlaskClient, data_fixture: List[Challenge]):
    set_config("CURRENT_ROUND", 1)
    response = client.get("/api/v2/challenges/2")
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data["id"] == 2
    assert "description" not in data
    assert "description_raw" not in data

    set_config("CURRENT_ROUND", 3)
    response = client.get("/api/v2/challenges/2")
    assert response.status_code == 404

def test_auth_team_get_detail_challenge(client: FlaskClient, data_fixture: List[Challenge]):
    access_token = create_access_token(identity={"team": {"id": 1, "name": "team 1"}})

    set_config("CURRENT_ROUND", 1)
    response = client.get("/api/v2/challenges/2", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data["id"] == 2
    assert "description" in data
    assert "description_raw" in data

    set_config("CURRENT_ROUND", 3)
    response = client.get("/api/v2/challenges/2", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 404

def test_invalid_token_team_get_detail_challenge(client: FlaskClient, data_fixture: List[Challenge]):
    team_not_exist = create_access_token(identity={"team": {"id": 999, "name": "team 1"}})

    set_config("CURRENT_ROUND", 1)
    response = client.get("/api/v2/challenges/2", headers={"Authorization": f"Bearer {team_not_exist}"})
    assert response.status_code == 401

    set_config("CURRENT_ROUND", 3)
    response = client.get("/api/v2/challenges/2", headers={"Authorization": f"Bearer {team_not_exist}"})
    assert response.status_code == 401

    expired_token = create_access_token(identity={"team": {"id": 999, "name": "team 1"}}, expires_delta=timedelta(days=-1))

    set_config("CURRENT_ROUND", 1)
    response = client.get("/api/v2/challenges/2", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401

    set_config("CURRENT_ROUND", 3)
    response = client.get("/api/v2/challenges/2", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401