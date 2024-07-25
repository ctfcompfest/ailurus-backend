from ailurus.models import db, Team
from flask.testing import FlaskClient
from typing import List
import pytest

@pytest.fixture
def team_data():
    teams = [
        Team(name="team 1", email="team1@mail.com", password="test"),
        Team(name="team 2", email="team2@mail.com", password="test"),
    ]
    db.session.add_all(teams)
    db.session.commit()
    return teams

def test_get_all_teams(client: FlaskClient, team_data: List[Team]):
    response = client.get("/api/v2/teams/")
    assert response.status_code == 200
    response_datas = response.get_json()['data']
    assert len(response_datas) == 2
    for data in response_datas:
        assert "email" not in data
        assert "password" not in data

def test_get_detail_team(client: FlaskClient, team_data: List[Team]):
    response = client.get("/api/v2/teams/1")
    assert response.status_code == 200
    response_data = response.get_json()['data']
    assert response_data["id"] == 1
    assert response_data["name"] == "team 1"
    assert "email" not in response_data
    assert "password" not in response_data


def test_fail_get_detail_team(client: FlaskClient, team_data: List[Team]):
    response = client.get("/api/v2/teams/100")
    assert response.status_code == 404
    assert response.get_json()["message"] == "team not found."