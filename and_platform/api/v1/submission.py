from and_platform.core.security import validteam_only, current_team
from and_platform.core.config import get_config, check_contest_is_running
from and_platform.core.submit import submit_flag
from flask import Blueprint, jsonify, request
from typing import List

submission_blueprint = Blueprint("submission", __name__)
submission_blueprint.before_request(validteam_only)

def bulk_submit(team_id: int, flags: List[str]):
    max_submit = get_config("MAX_BULK_SUBMIT", 100)
    if len(flags) > max_submit:
        return jsonify(status="failed", message=f"maximum {max_submit} flags at a time"), 400
    response = []
    for flag in flags:
        response.append(submit_flag(team_id, flag))
    return jsonify(status="success", data=response)

@submission_blueprint.post("/submit")
def flag_submission():
    if not check_contest_is_running():
        return jsonify(status="failed", message="contest has not started or finished."), 400
    
    req_body = request.get_json()
    if req_body.get("flags") != None:
        return bulk_submit(int(current_team.id), req_body.get("flags"))
    else:
        src_challid = req_body.get("challenge_id")
        if src_challid:
            src_challid = int(src_challid)
        src_flag = req_body.get("flag", "")
        
        resp = submit_flag(int(current_team.id), src_flag, src_challid)
        if resp['verdict'].find("correct") != -1:
            return jsonify(status="success", message=resp['verdict'], data=resp)
        else:
            return jsonify(status="failed", message=resp['verdict'], data=resp), 400