from flask import Blueprint, jsonify
from and_platform.api.v1.my.service import myservice_blueprint
from and_platform.core.config import get_config
from and_platform.core.security import validteam_only, current_team
from and_platform.models import ChallengeReleases, Solves

myapi_blueprint = Blueprint("myapi", __name__, url_prefix="/my")
myapi_blueprint.before_request(validteam_only)
myapi_blueprint.register_blueprint(myservice_blueprint)

@myapi_blueprint.get("/solves")
def get_my_solves():
    chall_release = ChallengeReleases.get_challenges_from_round(get_config("CURRENT_ROUND", 0))
    solves = Solves.query.with_entities(Solves.challenge_id).filter(
        Solves.team_id == current_team.id,
        Solves.challenge_id.in_(chall_release),
    ).all()
    solves = [elm[0] for elm in solves]

    return jsonify(status="success",data=solves)