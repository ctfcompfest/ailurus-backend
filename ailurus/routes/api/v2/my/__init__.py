from ailurus.utils.config import get_config
from ailurus.utils.svcmode import get_svcmode_module
from ailurus.utils.security import validteam_only, current_team
from ailurus.models import ChallengeRelease, Solve
from flask import Blueprint, jsonify, request

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

@myapi_blueprint.post("/challenges/<int:challenge_id>/service-manager/")
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

    return svcmodule.handler_svcmanager_request(
        team_id=current_team.id,
        challenge_id=challenge_id,
        request=request,
        is_solved=is_solved
    )