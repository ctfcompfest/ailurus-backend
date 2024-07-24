from ailurus.models import db, ProvisionMachine
from ailurus.schema import ProvisionMachineSchema
from flask import Blueprint, jsonify, request
from sqlalchemy import select
from typing import List, Tuple
from sqlalchemy.exc import IntegrityError

machine_blueprint = Blueprint("provision_machine", __name__, url_prefix="/machines")
machine_schema = ProvisionMachineSchema()

@machine_blueprint.get("/")
def get_all_machines():
    machines = ProvisionMachine.query.all()
    return jsonify(status="success", data=machine_schema.dump(machines, many=True))

@machine_blueprint.post("/")
def create_bulk_machines():
    machine_datas = request.get_json()
    if not isinstance(machine_datas, list):
        return jsonify(status="failed", message='input data should be a list of provision machines.'), 400

    machines: List[ProvisionMachine] = machine_schema.load(machine_datas, transient=True, many=True)
    machine_names: List[str] = [machine.name for machine in machines]
    if len(set(machine_names)) != len(machine_names):
        return jsonify(status="failed", message=f"provision machine name duplication found."), 400

    server_machine: Tuple[ProvisionMachine] | None = db.session.execute(
        select(ProvisionMachine).where(ProvisionMachine.name.in_(machine_names))
    ).first()
    if server_machine is not None:
        return jsonify(status="failed", message=f"provision machine with name='{server_machine[0].name}' has been registered."), 400
    
    db.session.add_all(machines)
    db.session.commit()

    return (
        jsonify(
            status="success",
            message="succesfully added new server.",
            data=machine_schema.dump(machines, many=True),
        ),
        200,
    )

@machine_blueprint.get("/<int:machine_id>")
def get_machine_detail(machine_id):
    machine = ProvisionMachine.query.filter_by(id=machine_id).first()

    if machine is None:
        return jsonify(status="not found", message="provision machine not found."), 404
    return (
        jsonify(
            status="success",
            data=machine_schema.dump(machine),
        ),
        200,
    )

@machine_blueprint.patch("/<int:machine_id>")
def update_machine(machine_id):
    machine: ProvisionMachine | None = ProvisionMachine.query.filter_by(id=machine_id).first()
    if machine is None:
        return jsonify(status="not found", message="provision machine not found."), 404

    json_data = request.get_json()
    machine_schema.load(json_data, transient=True, instance=machine, partial=True)
    try:
        db.session.commit()
        db.session.refresh(machine)
    except IntegrityError:
        db.session.rollback()
        return jsonify(status="failed", message=f"provision machine with name='{machine.name}' has been registered."), 400

    return (
        jsonify(
            status="success",
            message="{} info successfully updated.".format(machine.name),
            data=machine_schema.dump(machine),
        ),
        200,
    )

@machine_blueprint.delete("/<int:machine_id>")
def delete_machine(machine_id):
    machine = ProvisionMachine.query.filter_by(id=machine_id).first()
    if machine is None:
        return jsonify(status="not found", message="provision machine not found."), 404
    
    db.session.delete(machine)
    db.session.commit()

    return (
        jsonify(
            status="success",
            message=f"successfully deleted provision machine with id={machine_id}",
            data=machine_schema.dump(machine)
        ),
        200
    )
