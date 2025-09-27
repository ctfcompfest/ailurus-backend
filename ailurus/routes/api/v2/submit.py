from ailurus.models import (
    db,
    Challenge,
    ChallengeRelease,
    Flag,
    ManageServiceUnlockMode,
    Solve,
    Submission,
    Team,
)
from ailurus.utils.config import (
    is_contest_running,
    is_scoreboard_freeze,
    get_config,
    is_defense_phased,
)
from ailurus.utils.contest import calculate_submission_score
from ailurus.utils.security import validteam_only, current_team, limiter
from ailurus.utils.socket import send_attack_event
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from typing import List

submit_blueprint = Blueprint("submit", __name__, url_prefix="/submit")
submit_blueprint.before_request(validteam_only)


def submit_flag(team: Team, flag: str):
    current_tick = get_config("CURRENT_TICK", 0)
    current_round = get_config("CURRENT_ROUND", 0)
    chall_releases = ChallengeRelease.get_challenges_from_round(current_round)

    new_submission = Submission(
        team_id=team.id,
        round=current_round,
        tick=current_tick,
        value=flag,
    )
    flag_found = Flag.query.filter(
        Flag.value == flag,
        Flag.tick == current_tick,
        Flag.round == current_round,
        Flag.challenge_id.in_(chall_releases),
    ).first()
    if not flag_found:
        new_submission.verdict = False
        db.session.add(new_submission)
        db.session.commit()
        return {"flag": flag, "verdict": "flag is wrong or expired."}

    prev_correct_submission = Submission.query.filter(
        Submission.flag_id == flag_found.id,
        Submission.team_id == team.id,
        Submission.verdict == True,
    ).first()
    # Repeated correct submission will not be logged
    if prev_correct_submission:
        return {"flag": flag, "verdict": "flag already submitted."}

    prev_solve = Solve.query.filter_by(
        team_id=team.id, challenge_id=flag_found.challenge_id
    ).first()
    if prev_solve == None:
        if get_config("UNLOCK_MODE") == ManageServiceUnlockMode.SOLVE_FIRST.value:
            if flag_found.team_id == team.id:
                solve = Solve(team_id=team.id, challenge_id=flag_found.challenge_id)
                db.session.add(solve)
        else:
            solve = Solve(team_id=team.id, challenge_id=flag_found.challenge_id)
            db.session.add(solve)
    solved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    attacker = Team.query.filter(Team.id == team.id).first()
    defender = Team.query.filter(Team.id == flag_found.team_id).first()
    challenge = Challenge.query.filter(Challenge.id == flag_found.challenge_id).first()

    new_submission.verdict = True
    new_submission.flag_id = flag_found.id
    new_submission.challenge_id = flag_found.challenge_id
    new_submission.point = calculate_submission_score(
        attacker, defender, flag_found, challenge
    )
    db.session.add(new_submission)

    db.session.commit()
    # Emit attack event only when attacker and defender is different
    if (flag_found.team_id != team.id) and is_contest_running() and not is_scoreboard_freeze():
        send_attack_event(attacker, defender, challenge, solved_at)

    return {"flag": flag, "verdict": "flag is correct."}


def submit_flags(team: Team, flags: List[str]):
    return [submit_flag(team, flag) for flag in flags]


@submit_blueprint.post("/")
@limiter.limit("30 per second")
def bulk_submit_flag():
    if not is_contest_running():
        return jsonify(status="failed", message="contest is not running."), 400
    if is_defense_phased():
        return jsonify(status="failed", message="flag submission are not allowed in defense phase."), 400

    if "flags" in request.json:
        flags = request.get_json().get("flags")
        max_submit = get_config("MAX_BULK_SUBMIT", 100)
        if len(flags) > max_submit:
            return jsonify(status="failed", message=f"maximum {max_submit} flags at a time."), 400

        response = submit_flags(current_team, flags)
        return jsonify(status="success", data=response)
    elif "flag" in request.json:
        flag = request.get_json().get("flag")
        response = submit_flag(current_team, flag)
        if response["verdict"] == "flag is correct.":
            return jsonify(status="success", message=response["verdict"], data=response)
        else:
            return jsonify(status="failed", message=response["verdict"], data=response), 400

    return jsonify(status="failed", message="missing 'flags' field."), 400
