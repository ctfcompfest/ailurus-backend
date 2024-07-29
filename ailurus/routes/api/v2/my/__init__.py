from ailurus.utils.config import get_config
from ailurus.utils.svcmode import get_svcmode_module
from ailurus.utils.security import validteam_only, current_team
from ailurus.models import db, ManageServiceUnlockMode, CheckerResult, CheckerStatus, ChallengeRelease, Solve
from flask import Blueprint, jsonify, request
from sqlalchemy import func

import json

myapi_blueprint = Blueprint("myapi", __name__, url_prefix="/my")
myapi_blueprint.before_request(validteam_only)

@myapi_blueprint.get("/solves/")
def get_my_solves():
    chall_release = ChallengeRelease.get_challenges_from_round(get_config("CURRENT_ROUND", 0))
    solves = Solve.query.with_entities(Solve.challenge_id).filter(
        Solve.team_id == current_team.id,
        Solve.challenge_id.in_(chall_release),
    ).all()
    solves = [elm[0] for elm in solves]

    return jsonify(status="success", data=solves)

@myapi_blueprint.get("/allow-manage-services/")
def get_allowed_manage():
    chall_release = ChallengeRelease.get_challenges_from_round(get_config("CURRENT_ROUND", 0))
    solves = Solve.query.with_entities(Solve.challenge_id).filter(
        Solve.team_id == current_team.id,
        Solve.challenge_id.in_(chall_release),
    ).all()
    
    response = [elm[0] for elm in solves]
    if get_config("UNLOCK_MODE") == ManageServiceUnlockMode.NO_LOCK.value:
        response = chall_release

    return jsonify(status="success", data=response)


@myapi_blueprint.route("/challenges/<int:challenge_id>/service-manager/", methods=["GET", "POST"])
def handle_service_manager(challenge_id):
    chall_releases = ChallengeRelease.get_challenges_from_round(get_config("CURRENT_ROUND"))
    if challenge_id not in chall_releases:
        return jsonify(status="not found", message="challenge not found."), 404
    
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    solve = Solve.query.with_entities(Solve.challenge_id).filter(
        Solve.team_id == current_team.id,
        Solve.challenge_id == challenge_id,
    ).count()

    is_solved = solve >= 1
    is_allow_manage = is_solved
    if get_config("UNLOCK_MODE") == ManageServiceUnlockMode.NO_LOCK.value:
        is_allow_manage = True

    return svcmodule.handler_svcmanager_request(
        team_id=current_team.id,
        challenge_id=challenge_id,
        request=request,
        is_solved=is_solved,
        is_allow_manage=is_allow_manage
    )

@myapi_blueprint.get("/challenges/<int:challenge_id>/services-status/")
def get_service_status_by_challenge_id(challenge_id):
    team = current_team

    chall_release = ChallengeRelease.get_challenges_from_round(get_config("CURRENT_ROUND", 0))
    if challenge_id not in chall_release:
        return jsonify(status="not found.", message="challenge not found."), 404

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))

    latest_id = func.max(CheckerResult.id).label("latest_id")
    checker_result: Tuple[int, CheckerStatus, str] | None = db.session.query(
        latest_id,
        CheckerResult.status,
        CheckerResult.detail,
    ).where(
        CheckerResult.team_id == team.id,
        CheckerResult.challenge_id == challenge_id,
        CheckerResult.status.in_([
            CheckerStatus.FAULTY,
            CheckerStatus.VALID,
        ])
    ).group_by(
        CheckerResult.challenge_id,
        CheckerResult.team_id,
        CheckerResult.status,
        CheckerResult.detail,
    ).order_by(latest_id.desc()).first()
    
    if checker_result == None:
        return jsonify(status="success", data={"status": CheckerStatus.VALID, "detail": {}})

    _, checker_result_status, checker_result_detail = checker_result
    response = {
        "status": checker_result_status.value,
        "detail": svcmode.generator_public_services_status_detail(json.loads(checker_result_detail)),
    }

    return jsonify(status="success", data=response)