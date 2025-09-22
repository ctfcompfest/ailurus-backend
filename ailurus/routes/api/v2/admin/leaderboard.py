from ailurus.models import Challenge
from ailurus.utils.config import get_config, is_defense_phased
from ailurus.utils.svcmode import get_svcmode_module

from flask import Blueprint, request, jsonify

leaderboard_blueprint = Blueprint("admin_leaderboard", __name__)

@leaderboard_blueprint.get("/leaderboard/")
def get_admin_leaderboard():
    freeze_time = get_config("FREEZE_TIME")
    is_admin_version = not request.args.get("freeze")
    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    leaderboard = svcmode.get_leaderboard(freeze_time=freeze_time, is_admin=is_admin_version)

    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    challenges = Challenge.get_all_released_challenges(current_round)

    return jsonify(status="success", data=leaderboard, challenges=[{"id": chall.id, "title": chall.title} for chall in challenges])

