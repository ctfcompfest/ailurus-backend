from ailurus.models import db, Challenge, Team, CheckerResult, CheckerStatus
from flask.testing import FlaskClient
from typing import List, Tuple
import pytest
import json

@pytest.fixture
def data_fixtures() -> Tuple[List[Team], List[Challenge], List[CheckerResult]]:
    teams = [Team(name=f"team{i}", email=f"team{i}@mail.com", password="test") for i in range(2)]
    challenges = [
        Challenge(id=i, slug=f"chall{i}", title=f"Chall {i}", description="desc", testcase_checksum="test")
        for i in range(2)
    ]    
    db.session.add_all(teams)
    db.session.add_all(challenges)
    db.session.commit()
    
    checker_results = []
    for team in teams:
        for chall in challenges:
            for status in CheckerStatus:
                for tick in range(1, 3):
                    for round in range(1, 3):
                        tmp = CheckerResult(
                            team_id=team.id,
                            challenge_id=chall.id,
                            round=round,
                            tick=tick,
                            status=status,
                            detail=json.dumps({"key": "val"})
                        )
                        checker_results.append(tmp)
    db.session.add_all(checker_results)
    db.session.commit()

    return teams, challenges, checker_results


def test_get_checkerresults(client: FlaskClient, data_fixtures: Tuple[List[Team], List[Challenge], List[CheckerResult]]):
    accum_data_len = 0
    teams, challenges, _ = data_fixtures

    response = client.get("/api/v2/admin/checkresults/", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()
    accum_data_len += len(response_data['data'])
    assert "next_page" in response_data
    assert "prev_page" not in response_data

    response = client.get("/api/v2/admin/checkresults/?page=2", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()
    accum_data_len += len(response_data['data'])
    assert "next_page" not in response_data
    assert "prev_page" in response_data

    assert accum_data_len == CheckerResult.query.count()

    response = client.get("/api/v2/admin/checkresults/?page=999", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 404

    response = client.get(f"/api/v2/admin/checkresults/?team_id={teams[0].id}", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == CheckerResult.query.filter(CheckerResult.team_id == teams[0].id).count()

    response = client.get(f"/api/v2/admin/checkresults/?challenge_id={challenges[0].id}", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == CheckerResult.query.filter(CheckerResult.challenge_id == challenges[0].id).count()

    response = client.get(f"/api/v2/admin/checkresults/?round=1", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == CheckerResult.query.filter(CheckerResult.round == 1).count()

    response = client.get(f"/api/v2/admin/checkresults/?tick=1", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == CheckerResult.query.filter(CheckerResult.tick == 1).count()

    response = client.get(f"/api/v2/admin/checkresults/?status=0", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == CheckerResult.query.filter(CheckerResult.status == CheckerStatus.FAULTY).count()

    response = client.get(f"/api/v2/admin/checkresults/?status=1", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == CheckerResult.query.filter(CheckerResult.status == CheckerStatus.VALID).count()

    response = client.get(f"/api/v2/admin/checkresults/?round=1&status=1", headers={"X-ADCE-SECRET": "test"})
    assert len(response.get_json()['data']) == CheckerResult.query.filter(
            CheckerResult.status == CheckerStatus.VALID,
            CheckerResult.round == 1
        ).count()
    
    checkres_response = response.get_json()['data'][0]
    assert "id" in checkres_response
    assert checkres_response['status'] == 1
