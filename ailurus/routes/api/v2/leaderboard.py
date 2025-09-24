from ailurus.utils.config import get_config, is_contest_started, is_defense_phased
from ailurus.utils.scoremode import get_scoremode_module

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

    scoremode = get_scoremode_module(get_config("SCORE_SCRIPT"))
    leaderboard, challenges = scoremode.get_leaderboard(freeze_time=freeze_time)
    
    return jsonify(
        status="success",
        is_freeze=is_freeze,
        data=leaderboard,
        challenges=challenges,
    )