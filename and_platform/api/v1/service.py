from and_platform.models import ChallengeReleases, Services
from flask import Blueprint, jsonify
from and_platform.core.config import get_config

public_service_blueprint = Blueprint("public_service_blueprint", __name__, url_prefix="/services")

@public_service_blueprint.get("/")
def get_all_services():
    chall_release = ChallengeReleases.get_challenges_from_round(get_config("CURRENT_ROUND"))

    services = Services.query.order_by(
        Services.challenge_id,
        Services.team_id,
        Services.order
    ).filter(Services.challenge_id.in_(chall_release)).all()

    response = {}
    for service in services:
        resp_tmp = response.get(service.challenge_id, {})
        team_svc_tmp = resp_tmp.get(service.team_id, [])
        team_svc_tmp.append(service.address)
        
        resp_tmp[service.team_id] = team_svc_tmp
        response[service.challenge_id] = resp_tmp
    return jsonify(status="success", data=response)


@public_service_blueprint.get("/<int:chall_id>")
def get_service_by_challenge(chall_id):
    chall_release = ChallengeReleases.get_challenges_from_round(get_config("CURRENT_ROUND"))
    
    if chall_id not in chall_release:
        return jsonify(status="failed", message="challenge not found"), 404

    services = Services.query.order_by(
        Services.team_id,
        Services.order
    ).filter(Services.challenge_id == chall_id).all()

    response = {}
    for service in services:
        team_svc_tmp = response.get(service.team_id, [])
        team_svc_tmp.append(service.address)
        
        response[service.team_id] = team_svc_tmp
    return jsonify(status="success", data=response)
