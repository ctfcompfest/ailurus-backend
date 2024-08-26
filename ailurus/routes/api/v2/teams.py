from ailurus.models import Team
from ailurus.schema import TeamPublicSchema
from ailurus.utils.cache import cache
from flask import Blueprint, jsonify
from typing import List

public_team_blueprint = Blueprint("public_team", __name__, url_prefix="/teams")
team_schema = TeamPublicSchema()

@public_team_blueprint.get("/")
@cache.cached(timeout=15)
def get_all_teams():
    teams: List[Team] = Team.query.all()
    return jsonify(status="success", data=team_schema.dump(teams, many=True))

@public_team_blueprint.get("/<int:team_id>/")
@cache.cached(timeout=15)
def get_team_detail(team_id):
    team: Team | None = Team.query.filter_by(id=team_id).first()
    if not team:
        return jsonify(status="not found", message="team not found."), 404
    return jsonify(status="success", data=team_schema.dump(team))
