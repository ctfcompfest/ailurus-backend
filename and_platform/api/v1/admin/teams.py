from typing import Optional
from and_platform.core.config import get_config
from and_platform.models import db, Teams, Servers
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

import secrets

teams_blueprint = Blueprint("teams_blueprint", __name__, url_prefix="/teams")

@teams_blueprint.get("/")
def get_all_teams():
    teams = Teams.query.all()
    response = []
    for team in teams:
        response.append({
            "name": team.name,
            "email": team.email,
            "secret": team.secret,
            "server": {
                "id": team.server_id,
                "host": team.server_host,
            },
        })
    return (
        jsonify(
            status="success",
            data=response,
        ),
        200,
    )


@teams_blueprint.post("/")
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
        password=generate_password_hash(req_body["password"]),
        secret=secret_key,
    )
    db.session.add(new_team)

    server_mode = get_config("SERVER_MODE")
    if server_mode == "sharing":
        db.session.commit()
        data = {
            "id": new_team.id,
            "name": new_team.name,
            "secret": new_team.secret,
        }
        return (
            jsonify(
                status="success",
                message="team registered",
                data=data,
            ),
            200,
        )

    if "server_id" in req_body:
        server_id = req_body["server_id"]
        server: Optional[Servers] = Servers.query.filter_by(id=server_id).first()
        if server is None:
            return jsonify(status="failed", message="server cannot be found."), 400

        new_team.server_id = server_id
        new_team.server_host = server.host

    elif "server" in req_body:
        server_data = req_body["server"]
        server = Servers(
            host=server_data["host"],
            sshport=server_data["sshport"],
            username=server_data["username"],
            auth_key=server_data["auth_key"],
        )
        db.session.add(server)

        new_team.server_id = server.id
        new_team.server_host = server.host
    else:
        return (
            jsonify(
                status="failed",
                message="missing server details",
            ),
            400,
        )

    db.session.commit()
    data = {
        "id": new_team.id,
        "name": new_team.name,
        "secret": new_team.secret,
        "server": {"id": server.id, "host": server.host},
    }
    return (
        jsonify(
            status="success",
            message="team registered",
            data=data,
        ),
        200,
    )

@teams_blueprint.get("/<int:team_id>")
def get_team_detail(team_id):
    team = Teams.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404
    response = {
        "name": team.name,
        "email": team.email,
        "secret": team.secret,
        "server": {
            "id": team.server_id,
            "host": team.server_host,
        },
    }
    return (
        jsonify(
            status="success",
            data=response,
        ),
        200,
    )

@teams_blueprint.patch("/<int:team_id>")
def update_team(team_id):
    server_mode = get_config("SERVER_MODE")
    req_body = request.get_json()

    team = Teams.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404

    if "name" in req_body:
        team.name = req_body["name"]
    if "email" in req_body:
        team.email = req_body["email"]
    if "password" in req_body:
        team.password = generate_password_hash(req_body["password"])
    if server_mode == "private" and "server_id" in req_body:
        server = Servers.query.filter_by(id=req_body["server_id"]).first()
        if server is None:
            return jsonify(status="not found", message="server not found"), 404
        team.server_id = req_body["server_id"]
        team.server_host = server.host

    db.session.commit()
    db.session.refresh(team)

    data = {
        "id": team.id,
        "name": team.name,
    }

    if server_mode == "private":
        server = Servers.query.filter_by(id=team.server_id).first()
        data["server"] = {"id": server.id, "host": server.host}

    return (
        jsonify(
            status="success",
            message="{} info successfully updated.".format(team.name),
            data=data,
        ),
        200,
    )


@teams_blueprint.delete("/<int:team_id>")
def delete_team(team_id):
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
