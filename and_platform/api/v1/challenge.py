from and_platform.cache import cache
from and_platform.models import Challenges, ChallengeReleases
from flask import Blueprint, jsonify
from and_platform.core.config import get_config

import markdown

public_challenge_blueprint = Blueprint("public_challenge_blueprint", __name__, url_prefix="/challenges")


@public_challenge_blueprint.get("/")
@cache.memoize()
def get_all_challenge():
    visible_challenges = [] 
    visible_challenges_id = ChallengeReleases.get_challenges_from_round(get_config("CURRENT_ROUND", 0))
    challenges = Challenges.query.with_entities(
        Challenges.id,
        Challenges.name,
    ).filter(
        Challenges.id.in_(visible_challenges_id),
    ).order_by(Challenges.id).all()

    for challenge in challenges:
        data = {
            "id" : challenge[0],
            "name" : challenge[1]
        }
        visible_challenges.append(data)

    return jsonify(status="success", data=visible_challenges), 200

@public_challenge_blueprint.get("/<int:challenge_id>")
@cache.memoize()
def get_challenge_by_id(challenge_id):
    visible_challenges_id = ChallengeReleases.get_challenges_from_round(get_config("CURRENT_ROUND", 0))

    if challenge_id not in visible_challenges_id:
        return jsonify(status="failed", message="challenge not found"), 404

    challenge = Challenges.query.with_entities(Challenges.id, Challenges.name, Challenges.description).filter_by(id=challenge_id).first()
    data = {
            "id": challenge[0],
            "name": challenge[1],
            "description": markdown.markdown(challenge[2]),
            "description_raw": challenge[2],
        }
    return jsonify(status="success", data=data), 200