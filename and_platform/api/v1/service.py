from and_platform.models import ChallengeReleases, Services
from flask import Blueprint, jsonify
from and_platform.core.config import get_config

public_service_blueprint = Blueprint("public_service_blueprint", __name__, url_prefix="/services")

@public_service_blueprint.get("/")
def get_all_services():
    current_round = get_config("CURRENT_ROUND")
    chall_release = ChallengeReleases.query.with_entities(ChallengeReleases.challenge_id)\
        .filter(ChallengeReleases.round == current_round).all()
    chall_release = [elm[0] for elm in chall_release]

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
    current_round = get_config("CURRENT_ROUND")
    chall_release = ChallengeReleases.query.with_entities(ChallengeReleases.challenge_id)\
        .filter(ChallengeReleases.round == current_round, ChallengeReleases.challenge_id == chall_id).all()
    chall_release = [elm[0] for elm in chall_release]
    
    if chall_id not in chall_release:
        return jsonify(status="failed", message="challenge not found"), 404

    services = Services.query.order_by(
        Services.team_id,
        Services.order
    ).filter(Services.challenge_id.in_(chall_release)).all()

    response = {}
    for service in services:
        team_svc_tmp = response.get(service.team_id, [])
        team_svc_tmp.append(service.address)
        
        response[service.team_id] = team_svc_tmp
    return jsonify(status="success", data=response)
