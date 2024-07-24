from ailurus.models import db, Challenge, Team, Submission
from flask.testing import FlaskClient
from typing import List, Tuple
import pytest

@pytest.fixture
def data_fixtures() -> Tuple[List[Team], List[Challenge], List[Submission]]:
    team_datas = [{"name": f"team{i}", "email": f"team{i}@mail.com", "password": "test"} for i in range(3)]
    challenge_datas = [
        {"id": i, "slug": f"chall{i}", "title": f"Chall {i}", "description": "desc", "testcase_checksum":"test"}
        for i in range(3)
    ]
    
    teams = [Team(**team) for team in team_datas]
    challenges = [Challenge(**chall) for chall in challenge_datas]
    db.session.add_all(teams)
    db.session.add_all(challenges)
    db.session.commit()
    
    submissions = []
    for team in teams:
        for chall in challenges:
            for verdict in [True, False]:
                for tick in range(1, 3):
                    for round in range(1, 3):
                        subm = Submission(
                            team_id = team.id,
                            challenge_id = chall.id,
                            round = round,
                            tick = tick,
                            value = "test",
                            verdict = verdict,
                        )
                        submissions.append(subm)
    db.session.add_all(submissions)
    db.session.commit()

    return teams, challenges, submissions

def test_get_submissions(client: FlaskClient, data_fixtures: Tuple[List[Team], List[Challenge], List[Submission]]):
    teams, challenges, _ = data_fixtures

    response = client.get("/api/v2/admin/submissions/", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()
    assert "next_page" in response_data
    assert "prev_page" not in response_data

    response = client.get("/api/v2/admin/submissions/?page=2", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()
    assert "next_page" not in response_data
    assert "prev_page" in response_data

    response = client.get("/api/v2/admin/submissions/?page=999", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 404

    response = client.get(f"/api/v2/admin/submissions/?team_id={teams[0].id}", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == Submission.query.filter(Submission.team_id == teams[0].id).count()

    response = client.get(f"/api/v2/admin/submissions/?challenge_id={challenges[0].id}", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == Submission.query.filter(Submission.challenge_id == challenges[0].id).count()

    response = client.get(f"/api/v2/admin/submissions/?round=1", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == Submission.query.filter(Submission.round == 1).count()

    response = client.get(f"/api/v2/admin/submissions/?tick=1", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == Submission.query.filter(Submission.tick == 1).count()

    response = client.get(f"/api/v2/admin/submissions/?verdict=true", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == Submission.query.filter(Submission.verdict == True).count()

    response = client.get(f"/api/v2/admin/submissions/?verdict=false", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == Submission.query.filter(Submission.verdict == False).count()

    response = client.get(f"/api/v2/admin/submissions/?round=1&verdict=false", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == Submission.query.filter(
            Submission.verdict == False,
            Submission.round == 1
        ).count()