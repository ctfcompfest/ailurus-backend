from ailurus.models import db, Challenge, ChallengeRelease
from ailurus.utils.config import get_config
from ailurus.utils.cache import cache
from flask import Blueprint, jsonify
from flask_jwt_extended import (
    verify_jwt_in_request,
    current_user as current_team
)
from typing import List, Tuple
from sqlalchemy import select
import markdown

public_challenge_blueprint = Blueprint("public_challenge", __name__, url_prefix="/challenges")

@public_challenge_blueprint.get("/")
@cache.cached(timeout=60)
def get_all_visible_challenges():
    current_round = get_config("CURRENT_ROUND", 0)
    challs: List[Tuple[Challenge]] = db.session.execute(
        select(Challenge).where(
            Challenge.id.in_(
                ChallengeRelease.get_challenges_from_round(current_round)
            )
        ).order_by(Challenge.id)
    ).all()
    challs_data = [{"id": chall.id, "title": chall.title} for chall, in challs]

    return jsonify(status="success", data=challs_data)

@public_challenge_blueprint.get("/<int:challenge_id>/")
@cache.cached(timeout=60)
def get_detail_challenges(challenge_id):
    verify_jwt_in_request(optional=True)

    current_round = get_config("CURRENT_ROUND", 0)
    visible_challenge_ids = ChallengeRelease.get_challenges_from_round(current_round)
    if challenge_id not in visible_challenge_ids:
        return jsonify(status="not found", message="challenge not found."), 404

    chall: Challenge = Challenge.query.filter_by(id=challenge_id).first()
    chall_data = {
        "id": chall.id,
        "title": chall.title,
    }
    if current_team != None:
        chall_data.update({
            "description": markdown.markdown(chall.description),
            "description_raw": chall.description,
        })
        
    return jsonify(status="success", data=chall_data)