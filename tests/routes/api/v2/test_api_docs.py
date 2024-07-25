from ailurus.models import db, Team
from flask import current_app
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token

import pytest
import os

@pytest.fixture
def team_data():
    team = Team(email="mail@mail.com", name="team", password="test")
    db.session.add(team)
    db.session.commit()
    return team

def test_access_without_token(client: FlaskClient):
    response = client.get("/api/v2/docs/not_exist")
    assert response.status_code == 401

    not_exist_team = create_access_token(identity={"team": {"id": 999}})
    response = client.get("/api/v2/docs/not_exist", headers={"Authorization": f"Bearer {not_exist_team}"})
    assert response.status_code == 401

def test_access_not_exist_docs(client: FlaskClient, team_data: Team):
    access_token = create_access_token(identity={"team": {"id": 1}})
    response = client.get("/api/v2/docs/not_exist", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 404

def test_access_valid_docs(client: FlaskClient, team_data: Team):
    md_filepath = os.path.join(current_app.config["TEMPLATE_DIR"], "docs", "test.md")
    with open(md_filepath, "w+") as fp:
        fp.write("# Test")
    access_token = create_access_token(identity={"team": {"id": 1}})
    response = client.get("/api/v2/docs/test", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.get_json()['data'] == "<h1>Test</h1>"
    os.remove(md_filepath)