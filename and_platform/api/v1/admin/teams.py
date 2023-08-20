from and_platform.models import db, Teams, Servers
from and_platform.api.helper import convert_model_to_dict
from flask import Blueprint, jsonify, request
from and_platform.api.v1.admin.servers import create_new_server

import secrets
import json

teams_blueprint = Blueprint("teams_blueprint", __name__, url_prefix="/teams")

@teams_blueprint.route("/", methods=["POST"])
def create_team():
    req_body = request.get_json()

    try:
        email = req_body["email"]
        server_email = Teams.query.filter_by(email=email).first()
        if server_email is not None:
            return jsonify(status="failed", message="e-mail has been registered."), 409

        if 'server_id' in req_body:
            server_id = req_body["server_id"]
            server = Servers.query.filter_by(id=server_id).first()
            if server is None:
                return jsonify(status="failed", message="server cannot be found."), 400
            server = convert_model_to_dict(server)

            new_team = create_new_team(req_body, server_id, server["host"])
            
            data = {"id": new_team["id"], "name": new_team["name"], "server": {"id": server["id"], "host": server["host"]}, "secret": new_team["secret"]}

            return jsonify(status="success", message= "{} successfully created.".format(new_team["name"]), data=data), 200

        elif 'server' in req_body:
            server = req_body["server"]
            new_server = create_new_server(server)

            new_team = create_new_team(req_body, new_server["id"], new_server["host"])
            
            data = {"id": new_team["id"], "name": new_team["name"], "server": {"id": new_server["id"], "host": new_server["host"]}, "secret": new_team["secret"]}
            
            return jsonify(status="success", message= "{} successfully created.".format(new_team["name"]), data=data), 200

        else:
            raise Exception()

    except Exception as e:
        return jsonify(status="failed", message="attribute name, email, password, and server_id (or server) are required."), 400

@teams_blueprint.route("/<int:team_id>", methods=["PUT"])
def update_team(team_id):
    req_body = request.get_json()

    team = Teams.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404        
        
    if 'name' in req_body:
        team.name = req_body['name']
    if 'email' in req_body:
        team.email = req_body['email']
    if 'password' in req_body:
        team.password = req_body['password']
    if 'server_id' in req_body:
        server = Servers.query.filter_by(id=req_body['server_id']).first()
        if server is None:
            return jsonify(status="not found", message="server not found"), 404
        team.server_id = req_body['server_id']

    db.session.commit()
    db.session.refresh(team)
    team = convert_model_to_dict(team)

    server = Servers.query.filter_by(id=team["server_id"]).first()
    server = convert_model_to_dict(server)

    data = {"id": team["id"], "name": team["name"], "server": {"id": server["id"], "host": server["host"]}}

    return jsonify(status="success", message="{} info successfully updated.".format(team["name"]), data=data), 200

@teams_blueprint.route("/<int:team_id>", methods=["DELETE"])
def delete_team(team_id):
    req_body = request.get_json()

    team = Teams.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404        

    team_name = team.name
    db.session.delete(team)
    db.session.commit()

    return jsonify(status="success", message="{} successfully deleted.".format(team_name)), 200

def is_serializable(obj):
    try:
        jsonify(obj)
        return True
    except TypeError:
        return False    

def create_new_team(req_body, server_id, host):
    secret_key = secrets.token_hex(16)
    new_team = Teams(
        name = req_body["name"],
        email = req_body["email"],
        password = req_body["password"],
        server_id = server_id,
        server_host = host,
        secret = secret_key
    )
    db.session.add(new_team)
    db.session.commit()
    db.session.refresh(new_team)
    new_team = convert_model_to_dict(new_team)
    return new_team