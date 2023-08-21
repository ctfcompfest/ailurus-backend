from flask import Blueprint, jsonify
from and_platform.models import Teams
from and_platform.api.helper import convert_model_to_dict


public_teams_blueprint = Blueprint(
    "public_teams_blueprint", __name__, url_prefix="/teams"
)


@public_teams_blueprint.route("/", methods=["GET"])
def get_all_teams():
    teams = Teams.query.all()
    teams_data = []

    for team in teams:
        team_data = {
            "id": team.id,
            "name": team.name,
            "server": {"id": team.server_id, "host": team.server_host},
        }
        teams_data.append(team_data)

    return jsonify(status="success", data=teams_data), 200


@public_teams_blueprint.route("/<int:team_id>", methods=["GET"])
def get_team_by_id(team_id):
    team = Teams.query.filter_by(id=team_id).first()

    if team is None:
        return jsonify(status="not found", message="team not found"), 404

    team_data = {
        "id": team.id,
        "name": team.name,
        "server": {"id": team.server_id, "host": team.server_host},
    }

    return jsonify(status="success", data=team_data), 200
