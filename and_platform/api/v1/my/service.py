from and_platform.models import ChallengeReleases, Services, Servers, CheckerQueues, CheckerVerdict, Solves
from and_platform.core.config import get_config
from and_platform.core.service import do_patch, do_restart, do_reset, get_service_path, get_service_metadata
from and_platform.core.security import current_team
from flask import Blueprint, jsonify, request
import os

myservice_blueprint = Blueprint("myservice", __name__, url_prefix="/services/<int:challenge_id>")

@myservice_blueprint.before_request
def authorize_service():
    challenge_id = request.view_args.get('challenge_id', 0)
    if not Services.is_teamservice_exist(current_team.id, challenge_id):
        return jsonify(status="not found", message="service not found."), 404
    if not Solves.is_solved(current_team.id, challenge_id) or \
        challenge_id not in ChallengeReleases.get_challenges_from_round(get_config("CURRENT_ROUND")):
        return jsonify(status="forbidden", message="you have no access to this resource."), 403


@myservice_blueprint.post("/patch")
def myservice_patch(challenge_id):
    patch_dest = os.path.join(get_service_path(current_team.id, challenge_id), "patch", "service.patch")
    patch_file = request.files.get("patchfile")
    if not patch_file:
        return jsonify(status="failed", message="patch file is missing."), 400    
    patch_file.save(patch_dest)
    
    do_patch(
        current_team.id,
        challenge_id,
        Servers.get_server_by_mode(get_config("SERVER_MODE"), current_team.id, challenge_id)
    )
    
    return jsonify(status="success", message="patch submitted.")


@myservice_blueprint.post("/restart")
def myservice_restart(challenge_id):
    confirm_data: dict = request.get_json()
    if not confirm_data.get("confirm"):
        return jsonify(status="bad request", message="action not confirmed"), 400
    do_restart(
        current_team.id,
        challenge_id,
        Servers.get_server_by_mode(get_config("SERVER_MODE"), current_team.id, challenge_id)
    )
    return jsonify(status="success", message="restart request submitted.")


@myservice_blueprint.post("/reset")
def myservice_reset(challenge_id):
    confirm_data: dict = request.get_json()
    if not confirm_data.get("confirm"):
        return jsonify(status="bad request", message="action not confirmed"), 400
    do_reset(
        current_team.id,
        challenge_id,
        Servers.get_server_by_mode(get_config("SERVER_MODE"), current_team.id, challenge_id)
    )
    return jsonify(status="success", message="reset request submitted.")


@myservice_blueprint.get("/status")
def myservice_getstatus(challenge_id):
    checker_result = CheckerQueues.query.filter(
        CheckerQueues.challenge_id == challenge_id,
        CheckerQueues.team_id == current_team.id,
        CheckerQueues.result.in_([CheckerVerdict.FAULTY, CheckerVerdict.VALID]),
    ).order_by(CheckerQueues.id.desc()).first()
    
    response = CheckerVerdict.VALID.value
    if checker_result:
        response = checker_result.result.value
    return jsonify(status="success", data=response)
  

@myservice_blueprint.get("/meta")
def myservice_getmeta(challenge_id):
    response = get_service_metadata(
        current_team.id,
        challenge_id,
        Servers.get_server_by_mode(get_config("SERVER_MODE"), current_team.id, challenge_id)
    )
    return jsonify(status="success", data=response)
