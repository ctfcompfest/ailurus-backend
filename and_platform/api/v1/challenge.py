from and_platform.models import Challenges, ChallengeReleases
from and_platform.api.helper import convert_model_to_dict;
from flask import Blueprint, jsonify
from and_platform.core.config import get_config

from sqlalchemy import Row;

public_challenge_blueprint = Blueprint("public_challenge_blueprint", __name__, url_prefix="/challenges")


@public_challenge_blueprint.get("/")
def get_all_challenge():
    
    visible_challenges = [] 
    visible_challenges_id = get_all_released_challenge_id()   
    challenges = Challenges.query.with_entities(Challenges.id, Challenges.name, Challenges.description).filter(Challenges.id.in_(visible_challenges_id)).all()

    for challenge in challenges:
        data = {
            "id" : challenge[0],
            "name" : challenge[1],
            "descripttion" :challenge[2]
        }
        visible_challenges.append(data)

    return jsonify(status="success", data=visible_challenges), 200

@public_challenge_blueprint.get("/<int:challenge_id>")
def get_challenge_by_id(challenge_id):
    visible_challenges_id = get_all_released_challenge_id()

    if challenge_id not in visible_challenges_id:
        return jsonify(status="failed", message="challenge not found"), 404

    challenge = Challenges.query.with_entities(Challenges.id, Challenges.name, Challenges.description).filter_by(id=challenge_id).first()
    data = {
            "id" : challenge[0],
            "name" : challenge[1],
            "descripttion" :challenge[2]
        }
    return jsonify(status="success", data=data), 200

def get_all_released_challenge_id() -> list:
    current_round = get_config("CURRENT_ROUND")
    visible_challenges_id = []
    challenge_releases = ChallengeReleases.query.filter(ChallengeReleases.round <= current_round).all()

    if not isinstance(challenge_releases, list):
        challenge_releases = [challenge_releases]
    challenge_releases = convert_model_to_dict(challenge_releases)

    for release in challenge_releases:
        visible_challenges_id.append(release.get("challenge_id", 0))
    return visible_challenges_id