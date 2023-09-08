from flask import Blueprint, jsonify
from and_platform.cache import cache
from and_platform.models import Teams
from and_platform.core.config import get_config

public_teams_blueprint = Blueprint("public_teams_blueprint", __name__, url_prefix="/teams")

@public_teams_blueprint.get("/")
@cache.cached()
def get_all_teams():
    server_mode = get_config("SERVER_MODE")
    teams = Teams.query.all()
    teams_data = []

    for team in teams:
        team_data = {
            "id": team.id,
            "name": team.name,
        }
        if server_mode == "private":
            team_data["server"] = {"id": team.server_id, "host": team.server_host}
        teams_data.append(team_data)

    return jsonify(status="success", data=teams_data), 200


@public_teams_blueprint.get("/<int:team_id>")
@cache.cached()
def get_team_by_id(team_id):
    server_mode = get_config("SERVER_MODE")
    team = Teams.query.filter_by(id=team_id).first()

    if team is None:
        return jsonify(status="not found", message="team not found"), 404

    team_data = {
        "id": team.id,
        "name": team.name,
    }
    if server_mode == "private":
        team_data["server"] = {"id": team.server_id, "host": team.server_host}

    return jsonify(status="success", data=team_data), 200
