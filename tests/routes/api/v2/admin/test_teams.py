from ailurus.models import db, Team
from flask.testing import FlaskClient

def test_get_teams(client: FlaskClient):
    teams_data = [
        {'name': 'John Doe', 'email': 'john1@example.com', 'password': 'secret'},
        {'name': 'John Doe', 'email': 'john2@example.com', 'password': 'secret'}
    ]
    teams_email = [elm['email'] for elm in teams_data]

    for team in teams_data: db.session.add(Team(**team))
    db.session.commit()
    
    response = client.get('/api/v2/admin/teams/', headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200

    response_data = response.get_json()
    assert len(response_data['data']) == len(teams_data)
    for team in response_data['data']:
        assert team['email'] in teams_email

def test_create_teams(client: FlaskClient):
    # Simulate a POST request to create a new user
    response = client.post('/api/v2/admin/teams/', headers={
            "X-ADCE-SECRET": "test"
        }, json=[
            {'name': 'John Doe', 'email': 'john1@example.com', 'password': 'secret'},
            {'name': 'John Doe', 'email': 'john2@example.com', 'password': 'secret'}
        ])
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data['data']) == 2
    assert 'id' in data['data'][0]

    assert Team.query.count() == 2

def test_create_teams_failed(client: FlaskClient):
    team_data = {'name': 'John Doe', 'email': 'john1@example.com', 'password': 'secret'}
    response = client.post('/api/v2/admin/teams/', headers={
            "X-ADCE-SECRET": "test"
        }, json=team_data)
    assert response.status_code == 400
    
    response = client.post('/api/v2/admin/teams/', headers={
            "X-ADCE-SECRET": "test"
        }, json=[team_data, team_data])
    assert response.status_code == 400
    assert response.get_json()['message'].find('duplication') != -1

    response = client.post('/api/v2/admin/teams/', headers={
            "X-ADCE-SECRET": "test"
        }, json=[team_data, team_data])
    assert response.status_code == 400
    assert response.get_json()['message'].find('duplication') != -1
    
    db.session.add(Team(**team_data))
    db.session.commit()

    response = client.post('/api/v2/admin/teams/', headers={
            "X-ADCE-SECRET": "test"
        }, json=[team_data])
    assert response.status_code == 409
    assert response.get_json()['message'].find('registered') != -1


def test_get_teams_detail(client: FlaskClient):
    team_data = {'name': 'John Doe', 'email': 'john1@example.com', 'password': 'secret'}
    team = Team(**team_data)
    db.session.add(team)
    db.session.commit()

    team_id = team.id
    response = client.get(f'/api/v2/admin/teams/{team_id}', headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    
    response_data = response.get_json()['data']
    assert response_data['name'] == team_data['name']
    assert response_data['email'] == team_data['email']

    response = client.get(f'/api/v2/admin/teams/9999', headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 404

def test_patch_teams_detail(client: FlaskClient):
    team_data = {'name': 'John Doe', 'email': 'john1@example.com', 'password': 'secret'}
    team = Team(**team_data)
    db.session.add(team)
    db.session.commit()
    
    team_id = team.id
    response = client.patch(f'/api/v2/admin/teams/{team_id}', headers={"X-ADCE-SECRET": "test"}, json={
        "name": "Lolipop"
    })
    assert response.status_code == 200
    
    response = client.get(f'/api/v2/admin/teams/{team_id}', headers={"X-ADCE-SECRET": "test"})
    response_data = response.get_json()['data']
    assert response_data['name'] == "Lolipop"
    assert response_data['email'] == team_data['email']

    team = Team.query.first()
    assert team.name == "Lolipop"
    assert team.email == team_data['email']

def test_fail_teams_detail(client: FlaskClient):
    team_datas = [
        {'name': 'John Doe', 'email': 'john1@example.com', 'password': 'secret'},
        {'name': 'John Doe', 'email': 'john2@example.com', 'password': 'secret'}
    ]
    teams = [Team(**team_data) for team_data in team_datas]
    db.session.add_all(teams)
    db.session.commit()
    
    team_id = teams[0].id
    response = client.patch(f'/api/v2/admin/teams/{team_id}', headers={"X-ADCE-SECRET": "test"}, json={
        "email": "john2@example.com"
    })
    assert response.status_code == 400
    
    response = client.patch(f'/api/v2/admin/teams/9999', headers={"X-ADCE-SECRET": "test"}, json={
        "name": "Lolipop"
    })
    assert response.status_code == 404


def test_delete_teams(client: FlaskClient):
    team_data = {'name': 'John Doe', 'email': 'john1@example.com', 'password': 'secret'}
    team = Team(**team_data)
    db.session.add(team)
    db.session.commit()
    
    response = client.delete(f'/api/v2/admin/teams/9999', headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 404
    assert Team.query.count() == 1

    team_id = team.id
    response = client.delete(f'/api/v2/admin/teams/{team_id}', headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    assert Team.query.count() == 0
    
    
