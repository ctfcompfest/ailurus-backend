from ailurus.utils.config import get_config
from ailurus.utils.security import validteam_only, current_team
from ailurus.models import ChallengeRelease, Solve
from flask import Blueprint, jsonify

myapi_blueprint = Blueprint("myapi", __name__, url_prefix="/my")
myapi_blueprint.before_request(validteam_only)

@myapi_blueprint.get("/solves")
def get_my_solves():
    chall_release = ChallengeRelease.get_challenges_from_round(get_config("CURRENT_ROUND", 0))
    solves = Solve.query.with_entities(Solve.challenge_id).filter(
        Solve.team_id == current_team.id,
        Solve.challenge_id.in_(chall_release),
    ).all()
    solves = [elm[0] for elm in solves]

    return jsonify(status="success",data=solves)