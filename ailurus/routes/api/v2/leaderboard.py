from ailurus.utils.config import get_config, is_contest_started
from ailurus.utils.svcmode import get_svcmode_module
from flask import Blueprint, jsonify

leaderboard_blueprint = Blueprint("leaderboard", __name__)

@leaderboard_blueprint.get("/leaderboard")
def get_admin_leaderboard():
    if not is_contest_started():
        return jsonify(status="success", data=[])
    freeze_time = get_config("FREEZE_TIME")
    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    leaderboard = svcmode.get_leaderboard(freeze_time=freeze_time)
    return jsonify(status="success", data=leaderboard)