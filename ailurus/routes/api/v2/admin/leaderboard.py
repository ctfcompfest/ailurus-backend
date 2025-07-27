from ailurus.models import Challenge
from ailurus.utils.config import get_config
from ailurus.utils.svcmode import get_svcmode_module
from flask import Blueprint, request, jsonify

leaderboard_blueprint = Blueprint("admin_leaderboard", __name__)

@leaderboard_blueprint.get("/leaderboard/")
def get_admin_leaderboard():
    freeze_time = get_config("FREEZE_TIME")
    is_admin_version = not request.args.get("freeze")
    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    leaderboard = svcmode.get_leaderboard(freeze_time=freeze_time, is_admin=is_admin_version)
    challenges = Challenge.get_all_released_challenges(get_config("CURRENT_ROUND", 0))
    return jsonify(status="success", data=leaderboard, challenges={chall.id: chall.title for chall in challenges})