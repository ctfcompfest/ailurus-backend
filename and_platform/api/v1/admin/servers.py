from and_platform.core.security import admin_only;
from and_platform.models import db, Servers;
from flask import Blueprint, jsonify, request, views
from sqlalchemy import select;

servers_blueprint = Blueprint("servers_manager", __name__, url_prefix="/servers")
servers_blueprint.before_request(admin_only)

def get_existing_server_by_id(server_id) -> dict :
    server = Servers.query.filter_by(id=server_id).first()
    return {"server" : server, "is_exist": server is not None}

def get_existing_server_by_host(server_host) -> dict :
    server = Servers.query.filter_by(host=server_host).first()
    return {"server" : server, "is_exist": server is not None}

def convert_model_to_dict(model):
    model_data = model.__dict__
    model_data.pop('_sa_instance_state', None)
    return model_data

@servers_blueprint.route("/", methods=["GET"])
def get_all_servers():
    servers = Servers.query.all()
    servers_list = [convert_model_to_dict(server) for server in servers]
    return jsonify(status="success", data=servers_list), 200

@servers_blueprint.route("/<int:server_id>", methods=["GET"])
def get_server_by_id(server_id):
    server = get_existing_server_by_id(server_id)

    if not server["is_exist"]:
        return jsonify(status="not found", message="server not found"), 404
    
    return jsonify(status="success", data=convert_model_to_dict(server["server"])), 200


@servers_blueprint.route("/", methods=["POST"])
def add_server():
    req_body = request.get_json()

    if get_existing_server_by_host(req_body["host"])["is_exist"]:
        return jsonify(status="failed", message="server host must be unique."), 400
    
    new_server = Servers(
        host = req_body["host"],
        sshport = req_body["sshport"],
        username = req_body["username"],
        auth_key = req_body["auth_key"]
    )
    db.session.add(new_server)
    db.session.commit()

    new_server = get_existing_server_by_host(req_body["host"])

    return jsonify(status="success", message="succesfully added new server.", data=convert_model_to_dict(new_server["server"])), 200

@servers_blueprint.route("/<int:server_id>", methods=["PUT"])
def update_server(server_id):
    req_body = request.get_json()
    server_status = get_existing_server_by_id(server_id)

    if not server_status["is_exist"]:
        return jsonify(status="not found", message="server not found"), 404
    
    server_with_same_host = get_existing_server_by_host(req_body["host"])
    server = server_status["server"]

    if server_with_same_host["is_exist"] and server_with_same_host["server"].id != server.id:
        return jsonify(status="failed", message="There is already an existing server with the same host. please change your host to something unique."), 400
    
    

    if 'host' in req_body:
        server.host = req_body['host']
    if 'sshport' in req_body:
        server.sshport = req_body['sshport']
    if 'username' in req_body:
        server.username = req_body['username']
    if 'auth_key' in req_body:
        server.auth_key = req_body['auth_key']

    db.session.commit()

    updated_server_data = {
        "id": server.id,
        "host": server.host,
        "sshport": server.sshport,
        "username": server.username,
        "auth_key": server.auth_key
    }

    return jsonify(status="success", message="successfully updated server info.", data=updated_server_data), 200

@servers_blueprint.route("/<int:server_id>", methods=["DELETE"])
def delete(server_id):
    
    server = get_existing_server_by_id(server_id)

    if not server["is_exist"]:
        return jsonify(status="not found", message="server not found"), 404
    
    db.session.delete(server["server"])
    db.session.commit()

    return jsonify(status="success", message=f"successfully deleted server with id : {server_id}"), 200
    