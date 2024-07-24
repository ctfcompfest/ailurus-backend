from ailurus.models import db, ProvisionMachine
from flask.testing import FlaskClient
from typing import List
import json
import pytest

@pytest.fixture
def data_fixtures() -> List[ProvisionMachine]:
    machines = [
        ProvisionMachine(name=f"machine{i}", host="1.2.3.4", port=22, detail=json.dumps({"username": "root", "password": "test"}))
        for i in range(2)
    ]
    db.session.add_all(machines)
    db.session.commit()
    return machines

def test_get_machines(client: FlaskClient, data_fixtures: List[ProvisionMachine]):
    response = client.get("/api/v2/admin/machines/", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    response_data = response.get_json()
    assert len(response_data['data']) == len(data_fixtures)
    assert isinstance(response_data['data'][0]["id"], int)
    assert "username" in response_data['data'][0]['detail']
    assert "password" in response_data['data'][0]['detail']

def test_create_bulk_machines(client: FlaskClient, data_fixtures: List[ProvisionMachine]):
    machine_data = {
        "name": "machine100", "host": "1.2.3.4", "port": 22, "detail": json.dumps({"username": "root", "password": "test"})
    }

    response = client.post("/api/v2/admin/machines/", headers={"X-ADCE-SECRET": "test"}, json=[machine_data])
    response_data = response.get_json()
    assert response.status_code == 200
    assert len(response_data['data']) == 1
    assert isinstance(response_data['data'][0]["id"], int)
    assert ProvisionMachine.query.count() == 3

def test_failed_create_bulk_machines(client: FlaskClient, data_fixtures: List[ProvisionMachine]):
    machine_data = {
        "name": data_fixtures[0].name, "host": "1.2.3.4", "port": 22, "detail": json.dumps({"username": "root", "password": "test"})
    }

    response = client.post("/api/v2/admin/machines/", headers={"X-ADCE-SECRET": "test"}, json=machine_data)
    assert response.status_code == 400
    
    response = client.post("/api/v2/admin/machines/", headers={"X-ADCE-SECRET": "test"}, json=[machine_data])
    assert response.status_code == 400

    response = client.post("/api/v2/admin/machines/", headers={"X-ADCE-SECRET": "test"}, json=[machine_data, machine_data])
    assert response.status_code == 400

def test_get_machine_detail(client: FlaskClient, data_fixtures: List[ProvisionMachine]):
    machine = data_fixtures[0]
    response = client.get(f"/api/v2/admin/machines/{machine.id}", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == machine.name

    response = client.get(f"/api/v2/admin/machines/999", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 404

def test_patch_machine(client: FlaskClient, data_fixtures: List[ProvisionMachine]):
    machine = data_fixtures[0]
    patch_detail = {"haha": "hihi"}
    response = client.patch(
        f"/api/v2/admin/machines/{machine.id}",
        headers={"X-ADCE-SECRET": "test"},
        json={"name": "Mymachine", "detail": patch_detail}
    )

    machine_db = ProvisionMachine.query.filter_by(id=machine.id).first()
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == "Mymachine"
    assert machine_db.name == "Mymachine"
    assert machine_db.host == machine.host
    assert json.loads(machine_db.detail) == patch_detail
    
    response = client.patch(
        f"/api/v2/admin/machines/{machine.id}",
        headers={"X-ADCE-SECRET": "test"},
        json={"name": "anotherName"}
    )
    machine_db = ProvisionMachine.query.filter_by(id=machine.id).first()
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == "anotherName"
    assert machine_db.name == "anotherName"
    

def test_fail_patch_machine(client: FlaskClient, data_fixtures: List[ProvisionMachine]):
    response = client.patch(
        f"/api/v2/admin/machines/9999",
        headers={"X-ADCE-SECRET": "test"},
        json={"name": "Mymachine"}
    )
    assert response.status_code == 404
    
    response = client.patch(
        f"/api/v2/admin/machines/{data_fixtures[0].id}",
        headers={"X-ADCE-SECRET": "test"},
        json={"name": data_fixtures[1].name}
    )
    assert response.status_code == 400

def test_delete_machine(client: FlaskClient, data_fixtures: List[ProvisionMachine]):
    machine = data_fixtures[0]
    response = client.delete(f"/api/v2/admin/machines/{machine.id}", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == machine.name
    assert ProvisionMachine.query.count() == 1

    response = client.delete(f"/api/v2/admin/machines/999", headers={"X-ADCE-SECRET": "test"})
    assert response.status_code == 404

