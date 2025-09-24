from ailurus.utils.config import get_config
from ailurus.utils.scoremode import get_scoremode_module

from flask import Blueprint, request, jsonify

leaderboard_blueprint = Blueprint("admin_leaderboard", __name__)

@leaderboard_blueprint.get("/leaderboard/")
def get_admin_leaderboard():
    freeze_time = get_config("FREEZE_TIME")
    is_admin_version = not request.args.get("freeze")
    scoremode = get_scoremode_module(get_config("SCORE_SCRIPT"))
    leaderboard, challenges = scoremode.get_leaderboard(freeze_time=freeze_time, is_admin=is_admin_version)

    return jsonify(status="success", data=leaderboard, challenges=challenges)

