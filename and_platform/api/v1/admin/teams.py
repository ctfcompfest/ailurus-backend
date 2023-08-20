from typing import Optional
from and_platform.core.config import get_config
from and_platform.models import db, Teams, Servers
from and_platform.api.helper import convert_model_to_dict
from flask import Blueprint, jsonify, request

import secrets
import json

teams_blueprint = Blueprint("teams_blueprint", __name__, url_prefix="/teams")


@teams_blueprint.route("/", methods=["POST"])
def create_team():
    req_body = request.get_json()

    email = req_body["email"]
    server_email = Teams.query.filter_by(email=email).first()
    if server_email is not None:
        return jsonify(status="failed", message="e-mail has been registered."), 409

    secret_key = secrets.token_hex(16)
    new_team = Teams(
        name=req_body["name"],
        email=req_body["email"],
        password=req_body["password"],
        secret=secret_key,
    )
    db.session.add(new_team)
    db.session.commit()

    data = {
        "id": new_team.id,
        "name": new_team.name,
        "secret": new_team.secret,
    }

    server_mode = get_config("SERVER_MODE")
    if server_mode == "sharing":
        return (
            jsonify(
                status="success",
                message="team registered",
                data=data,
            ),
            200,
        )

    if "server_id" not in req_body and "server" not in req_body:
        return (
            jsonify(
                status="failed",
                message="missing server details",
            ),
            400,
        )

    if "server_id" in req_body:
        server_id = req_body["server_id"]
        server: Optional[Servers] = Servers.query.filter_by(id=server_id).first()
        if server is None:
            return jsonify(status="failed", message="server cannot be found."), 400

        new_team.server_id = server_id
        new_team.server_host = server.host

        data["server"] = {"id": server.id, "host": server.host}

    elif "server" in req_body:
        server = req_body["server"]
        new_server = Servers(
            host=server["host"],
            sshport=server["sshport"],
            username=server["username"],
            auth_key=server["auth_key"],
        )
        db.session.add(new_server)
        db.session.commit()

        new_team.server_id = server_id
        new_team.server_host = server.host

        data["server"] = {"id": new_server.id, "host": new_server.host}

    return (
        jsonify(
            status="success",
            message="team registered",
            data=data,
        ),
        200,
    )


@teams_blueprint.route("/<int:team_id>", methods=["PUT"])
def update_team(team_id):
    req_body = request.get_json()

    team = Teams.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404

    if "name" in req_body:
        team.name = req_body["name"]
    if "email" in req_body:
        team.email = req_body["email"]
    if "password" in req_body:
        team.password = req_body["password"]
    if "server_id" in req_body:
        server = Servers.query.filter_by(id=req_body["server_id"]).first()
        if server is None:
            return jsonify(status="not found", message="server not found"), 404
        team.server_id = req_body["server_id"]
        team.server_host = server.host

    db.session.commit()
    db.session.refresh(team)
    team = convert_model_to_dict(team)

    server = Servers.query.filter_by(id=team["server_id"]).first()
    server = convert_model_to_dict(server)

    data = {
        "id": team["id"],
        "name": team["name"],
        "server": {"id": server["id"], "host": server["host"]},
    }

    return (
        jsonify(
            status="success",
            message="{} info successfully updated.".format(team["name"]),
            data=data,
        ),
        200,
    )


@teams_blueprint.route("/<int:team_id>", methods=["DELETE"])
def delete_team(team_id):
    req_body = request.get_json()

    team = Teams.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404

    team_name = team.name
    db.session.delete(team)
    db.session.commit()

    return (
        jsonify(status="success", message="{} successfully deleted.".format(team_name)),
        200,
    )


def is_serializable(obj):
    try:
        jsonify(obj)
        return True
    except TypeError:
        return False
