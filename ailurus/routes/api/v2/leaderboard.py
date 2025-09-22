from ailurus.utils.config import get_config, is_contest_started, is_defense_phased
from ailurus.utils.svcmode import get_svcmode_module
from ailurus.models import Challenge

from flask import Blueprint, jsonify
from ailurus.utils.cache import cache

from datetime import datetime, timezone

public_leaderboard_blueprint = Blueprint("leaderboard", __name__)

@public_leaderboard_blueprint.get("/leaderboard/")
@cache.cached(timeout=45)
def get_public_leaderboard():
    if not is_contest_started():
        return jsonify(status="success", data=[])

    freeze_time = get_config("FREEZE_TIME")
    is_freeze = datetime.now(timezone.utc) >= freeze_time

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    leaderboard = svcmode.get_leaderboard(freeze_time=freeze_time)
    
    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    challenges = Challenge.get_all_released_challenges(current_round)
    
    return jsonify(
        status="success",
        is_freeze=is_freeze,
        data=leaderboard,
        challenges=[{"id": chall.id, "title": chall.title} for chall in challenges],
    )