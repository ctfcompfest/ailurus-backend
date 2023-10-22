from flask import Blueprint, request, jsonify
from and_platform.core.config import get_config
from and_platform.core.security import gateflag_only
from and_platform.models import db, Teams, Servers, Flags

flagserverapi_blueprint = Blueprint("flagserver", __name__, url_prefix="/flagserver")
flagserverapi_blueprint.before_request(gateflag_only)

class FlagNotFoundException(Exception):
    """Exception for flag not found"""

def get_flag_by_serverip(subid: int) -> str:
    target_identifier = request.headers.get("x-source-ip", None)
    challenge_id = request.get_json().get("challenge_id", 1)

    current_tick = get_config("CURRENT_TICK")
    current_round = get_config("CURRENT_ROUND")

    team_id = db.session.query(Teams.id).join(Servers, Servers.id == Teams.server_id).filter(Servers.host == target_identifier).scalar()
    if team_id == None:
        raise FlagNotFoundException(f"Team for '{target_identifier}' cannot be found.")

    flag_value = (
        db.session.query(Flags.value).filter(
            Flags.round == current_round,
            Flags.tick == current_tick,
            Flags.challenge_id == challenge_id,
            Flags.team_id == team_id,
            Flags.subid == subid,
        ).scalar()
    )
    if flag_value == None:
        raise FlagNotFoundException(f"Flag cannot be found.")
    return flag_value

def get_flag_api_handler(subid):
    SUBID_TRANSFORM = {
        1: "user",
        2: "root",
    }
    data_resp = {
        "type": SUBID_TRANSFORM[subid],
        "generated_at": "tick " + get_config("CURRENT_TICK"),
    }

    try:
        flag_value = get_flag_by_serverip(subid)
        data_resp["flag"] = flag_value
    except FlagNotFoundException as e:
        return jsonify(status="failed", message=str(e))
    return jsonify(status="ok", data=data_resp)

@flagserverapi_blueprint.post("/user_flag")
def user_flag():
    return get_flag_api_handler(1)

@flagserverapi_blueprint.post("/root_flag")
def root_flag():
    return get_flag_api_handler(2)
