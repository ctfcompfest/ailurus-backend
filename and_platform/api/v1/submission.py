from and_platform.core.security import validteam_only, current_team
from and_platform.core.config import get_config, check_contest_is_running
from and_platform.models import db, ChallengeReleases, Flags, Submissions, Solves
from flask import Blueprint, jsonify, request
from typing import List

submission_blueprint = Blueprint("submission", __name__)
submission_blueprint.before_request(validteam_only)

def submit_flag(team_id: int, flag: str, chall_id: int | None = None):
    current_tick = get_config("CURRENT_TICK", 0)
    current_round = get_config("CURRENT_ROUND", 0)
    chall_releases = ChallengeReleases.get_challenges_from_round(current_round)
    
    new_submission = Submissions(
        team_id=team_id,
        challenge_id=chall_id,
        round=current_round,
        tick=current_tick,
        value=flag,
    )

    flag_found = Flags.query.filter(
        Flags.value == flag,
        Flags.tick == current_tick,
    ).first()
    print((flag_found == None), (flag_found.challenge_id not in chall_releases), (chall_id not in chall_releases))
    if (flag_found == None) or \
        (flag_found.challenge_id not in chall_releases) or \
        (chall_id != None and chall_id not in chall_releases) or \
        (chall_id != None and flag_found.challenge_id != chall_id):
       new_submission.verdict = False
       db.session.add(new_submission)
       return {"flag": flag, "verdict": "flag is wrong or expired."}
    
    prev_correct_submission = Submissions.query.filter(
        Submissions.flag_id == flag_found.id,
        Submissions.team_id == team_id,
        Submissions.verdict == True,
    ).first()
    # Repeated correct submission will not be logged
    if prev_correct_submission:
       return {"flag": flag, "verdict": "flag already submitted."}

    new_submission.verdict = True
    new_submission.flag_id = flag_found.id
    new_submission.challenge_id = flag_found.challenge_id
    db.session.add(new_submission)

    prev_solve = Solves.query.filter_by(team_id=team_id, challenge_id=flag_found.challenge_id).first()
    if prev_solve == None:
        solve = Solves(team_id=current_team.id, challenge_id=flag_found.challenge_id)
        db.session.add(solve)
    db.session.commit()
    return {"flag": flag, "verdict": "flag is correct."}

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
    # if not check_contest_is_running():
    #     return jsonify(status="failed", message="contest has not started or finished."), 400
    
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