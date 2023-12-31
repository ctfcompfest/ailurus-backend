from and_platform.cache import cache
from and_platform.core.config import get_config, check_contest_is_started, check_contest_is_finished
from flask import Blueprint, jsonify

public_contest_blueprint = Blueprint("public_contest_blueprint", __name__, url_prefix="/contest")

@public_contest_blueprint.get("/info")
@cache.cached(timeout=60)
def get_contest_config():
    event_name = get_config("EVENT_NAME", "AnD")
    start_time = get_config("START_TIME")
    number_round = get_config("NUMBER_ROUND", 0)
    number_tick = get_config("NUMBER_TICK", 0)
    tick_duration = get_config("TICK_DURATION", 0)
    event_status = {}
    current_round = get_config("CURRENT_ROUND", 0)
    current_tick = get_config("CURRENT_TICK", 0)
    logo_url = get_config("LOGO_URL", "")

    if not check_contest_is_started():
        event_status["state"] = "not started"
    elif check_contest_is_finished():
        event_status["state"] = "finished"
    else:
        event_status["state"] = "running"
        event_status["current_round"] = current_round
        event_status["current_tick"] = current_tick
    
    info = {
        "event_name" : event_name,
        "event_status" : event_status,
        "start_time" : start_time.isoformat(),
        "number_round" : number_round,
        "number_tick" : number_tick,
        "tick_duration" : tick_duration,
        "logo_url": logo_url,
    }

    return jsonify(status="success", data=info), 200