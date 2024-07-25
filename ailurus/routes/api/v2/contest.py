from ailurus.utils.config import (
    get_config,
    is_contest_running,
    is_contest_finished,
    is_contest_paused,
    is_contest_started
)
from flask import Blueprint, jsonify

contestinfo_blueprint = Blueprint("contestinfo", __name__, url_prefix="/contest")

@contestinfo_blueprint.get("/info")
def get_contest_info():
    if not is_contest_started():
        event_status = "not started"
    elif is_contest_running():
        event_status = "running"
    elif is_contest_finished():
        event_status = "finished"
    elif is_contest_paused(): 
        event_status = "paused"
    
    response_data = {
        "event_name": get_config("EVENT_NAME"),
        "logo_url": get_config("LOGO_URL"),
        "start_time": get_config("START_TIME").isoformat(),
        "number_round": get_config("NUMBER_ROUND"),
        "number_tick": get_config("NUMBER_TICK"),
        "current_round": get_config("CURRENT_ROUND", 0),
        "current_tick": get_config("CURRENT_TICK", 0),
        "event_status": event_status,
    }
    return jsonify(status="success", data=response_data)