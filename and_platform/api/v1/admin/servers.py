from and_platform.models import db, Servers;
from and_platform.api.helper import convert_model_to_dict;
from flask import Blueprint, jsonify, request;

servers_blueprint = Blueprint("servers_manager", __name__, url_prefix="/servers")

@servers_blueprint.get("/")
def get_all_servers():
    servers = Servers.query.all()
    servers = convert_model_to_dict(servers)

    return jsonify(status="success", data=servers), 200

@servers_blueprint.get("/<int:server_id>")
def get_by_id(server_id):
    server = Servers.query.filter_by(id=server_id).first()

    if server is None:
        return jsonify(status="not found", message="server not found"), 404
    server = convert_model_to_dict(server)

    return jsonify(status="success", data=server), 200


@servers_blueprint.post("/")
def add_server():
    req_body = request.get_json()

    if Servers.is_exist_with_host(req_body.get("host", "127.0.0.1")):
        return jsonify(status="failed", message="server host must be unique."), 400
    try:
        new_server = Servers(
            host = req_body["host"],
            sshport = req_body["sshport"],
            username = req_body["username"],
            auth_key = req_body["auth_key"]
        )
    except KeyError:
        return jsonify(status="failed", message="missing required attributes.")
    
    db.session.add(new_server)
    db.session.commit()
    db.session.refresh(new_server) # update the object with newest commit
    new_server = convert_model_to_dict(new_server)

    return jsonify(status="success", message="succesfully added new server.", data=new_server), 200

@servers_blueprint.patch("/<int:server_id>")
def update_server(server_id):
    req_body = request.get_json()

    server = Servers.query.filter_by(id=server_id).first()
    if server is None:
        return jsonify(status="not found", message="server not found"), 404
    
    new_host = req_body.get("host", server.host)

    if server.host != new_host:
        if Servers.is_exist_with_host(new_host):
            return jsonify(status="failed", message="host must be unique"), 400
        
    if 'host' in req_body:
        server.host = req_body['host']
    if 'sshport' in req_body:
        server.sshport = req_body['sshport']
    if 'username' in req_body:
        server.username = req_body['username']
    if 'auth_key' in req_body:
        server.auth_key = req_body['auth_key']

    db.session.commit()
    db.session.refresh(server)
    updated_server_data = convert_model_to_dict(server)

    return jsonify(status="success", message="successfully updated server info.", data=updated_server_data), 200

@servers_blueprint.delete("/<int:server_id>")
def delete(server_id):
    
    server = Servers.query.filter_by(id=server_id).first()
    if server is None:
        return jsonify(status="not found", message="server not found"), 404
    
    db.session.delete(server)
    db.session.commit()

    return jsonify(status="success", message=f"successfully deleted server with id : {server_id}"), 200
