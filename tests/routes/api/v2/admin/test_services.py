from ailurus.models import db, Challenge, Team, Service
from flask.testing import FlaskClient
from typing import List, Tuple
import json
import pytest

@pytest.fixture
def data_fixtures() -> Tuple[List[Team], List[Challenge], List[Service]]:
    teams = [Team(name=f"team{i}", email=f"team{i}@mail.com", password="test") for i in range(4)]
    challenges = [
        Challenge(id=i, slug=f"chall{i}", title=f"Chall {i}", description="desc", testcase_checksum="test")
        for i in range(4)
    ]    
    db.session.add_all(teams)
    db.session.add_all(challenges)
    db.session.commit()
    
    services = []
    for team in teams:
        for chall in challenges:
            for i in range(4):
                services.append(Service(
                    team_id=team.id,
                    challenge_id=chall.id,
                    order=i,
                    secret="secret",
                    detail=json.dumps({"key1":"val1","key2":"val2"})
                ))
    db.session.add_all(services)
    db.session.commit()

    return teams, challenges, services

def test_get_services(client: FlaskClient, data_fixtures: Tuple[List[Team], List[Challenge], List[Service]]):
    accum_data_len = 0

    response = client.get("/api/v2/admin/services/", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()
    accum_data_len += len(response_data['data'])
    assert "next_page" in response_data
    assert "prev_page" not in response_data

    response = client.get("/api/v2/admin/services/?page=2", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()
    accum_data_len += len(response_data['data'])
    assert "next_page" not in response_data
    assert "prev_page" in response_data

    assert accum_data_len == Service.query.count()