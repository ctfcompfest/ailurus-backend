from ailurus.models import db, Challenge, ChallengeRelease, CheckerResult, CheckerStatus, Team, Service
from ailurus.utils.config import get_config
from ailurus.utils.security import validteam_only
from ailurus.utils.svcmode import get_svcmode_module
from flask import Blueprint, jsonify
from sqlalchemy import and_, select, func
from typing import List, Tuple, Any

import itertools

__all__ = ["public_services_blueprint", "auth_services_blueprint"]

public_services_blueprint = Blueprint("public_services", __name__)

@public_services_blueprint.get("/services-status")
def get_all_services_status():
    chall_release = ChallengeRelease.get_challenges_from_round(get_config("CURRENT_ROUND", 0))

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    latest_id = func.max(CheckerResult.id).label("latest_id")
    checker_results: List[Tuple[Any, CheckerResult]] = db.session.query(
        latest_id,
        CheckerResult,
    ).where(
        CheckerResult.challenge_id.in_(chall_release),
        CheckerResult.result.in_([
            CheckerStatus.FAULTY,
            CheckerStatus.VALID,
        ])
    ).group_by(
        CheckerResult.challenge_id,
        CheckerResult.team_id,
        CheckerResult.result,
    ).order_by(latest_id.desc()).all()
    
    response = {}
    for _, checker_result in checker_results:
        chall_data = response.get(checker_result.challenge_id, {})
        if checker_result.team_id in chall_data: continue

        chall_data[checker_result.team_id] = {
            "status": checker_result.status.value,
            "detail": svcmode.generator_public_services_status_detail(checker_result),
        }
        response[checker_result.challenge_id] = chall_data

    return jsonify(status="success", data=response)



@public_services_blueprint.get("/teams/<int:team_id>/services-status")
def get_all_services_status_from_team(team_id):
    team = Team.query.filter_by(id=team_id).first()
    if not team:
        return jsonify(status="not found.", message="team not found."), 404

    chall_release = ChallengeRelease.get_challenges_from_round(get_config("CURRENT_ROUND", 0))

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    latest_id = func.max(CheckerResult.id).label("latest_id")
    checker_results: List[Tuple[Any, CheckerResult]] = db.session.query(
        latest_id,
        CheckerResult,
    ).where(
        CheckerResult.team_id == team_id,
        CheckerResult.challenge_id.in_(chall_release),
        CheckerResult.result.in_([
            CheckerStatus.FAULTY,
            CheckerStatus.VALID,
        ])
    ).group_by(
        CheckerResult.challenge_id,
        CheckerResult.team_id,
        CheckerResult.result,
    ).order_by(latest_id.desc()).all()
    
    response = {}
    for _, checker_result in checker_results:
        if checker_result.challenge_id in response: continue
        response[checker_result.challenge_id] = {
            "status": checker_result.status.value,
            "detail": svcmode.generator_public_services_status_detail(checker_result),
        }

    return jsonify(status="success", data=response)


@public_services_blueprint.get("/challenges/<int:challenge_id>/services-status")
def get_all_services_status_from_challenge(challenge_id):
    chall_release = ChallengeRelease.get_challenges_from_round(get_config("CURRENT_ROUND", 0))

    if challenge_id not in chall_release:
        return jsonify(status="not found.", message="challenge not found."), 404

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    latest_id = func.max(CheckerResult.id).label("latest_id")
    checker_results: List[Tuple[Any, CheckerResult]] = db.session.query(
        latest_id,
        CheckerResult,
    ).where(
        CheckerResult.challenge_id.in_(chall_release),
        CheckerResult.result.in_([
            CheckerStatus.FAULTY,
            CheckerStatus.VALID,
        ])
    ).group_by(
        CheckerResult.challenge_id,
        CheckerResult.team_id,
        CheckerResult.result,
    ).order_by(latest_id.desc()).all()
    
    response = {}
    for _, checker_result in checker_results:
        if checker_result.team_id in response: continue
        response[checker_result.team_id] = {
            "status": checker_result.status.value,
            "detail": svcmode.generator_public_services_status_detail(checker_result),
        }

    return jsonify(status="success", data=response)


auth_services_blueprint = Blueprint("auth_services", __name__)
auth_services_blueprint.before_request(validteam_only)

@auth_services_blueprint.get("/services")
def get_all_services():
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    release_challs: List[Challenge] = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(ChallengeRelease.round == get_config("CURRENT_ROUND", 0))
        ).scalars().all()
    teams: List[Team] = Team.query.all()
    
    response = {}
    for chall, team in itertools.product(release_challs, teams):
        services: List[Service] = db.session.execute(
            select(Service).where(
                and_(
                    Service.challenge_id == chall.id,
                    Service.team_id == team.id
                )
            )
        ).scalars().all()
        
        svcinfo = svcmodule.generator_public_services_info(team=team, challenge=chall, services=services)
        chall_data = response.get(chall.id, {})
        chall_data[team.id] = svcinfo
        response[chall.id] = chall_data

    return jsonify(status="success", data=response)

@auth_services_blueprint.get("/teams/<int:team_id>/services")
def get_all_services_from_team(team_id):
    team: Team = Team.query.filter_by(id=team_id).first()
    if not team:
        return jsonify(status="not found", message="team not found."), 404
    
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    release_challs: List[Challenge] = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(ChallengeRelease.round == get_config("CURRENT_ROUND", 0))
        ).scalars().all()
    
    response = {}
    for chall in release_challs:
        services: List[Service] = db.session.execute(
            select(Service).where(
                and_(
                    Service.challenge_id == chall.id,
                    Service.team_id == team.id
                )
            )
        ).scalars().all()
        
        svcinfo = svcmodule.generator_public_services_info(team=team, challenge=chall, services=services)
        chall_data = response.get(chall.id, {})
        chall_data[team.id] = svcinfo
        response[chall.id] = chall_data

    return jsonify(status="success", data=response)


@auth_services_blueprint.get("/challenges/<int:challenge_id>/services")
def get_all_services_from_challenge(challenge_id):
    chall: Challenge = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(
                ChallengeRelease.round == get_config("CURRENT_ROUND", 0),
                Challenge.challenge_id == challenge_id
            )
        ).scalars().first()
    if not chall:
        return jsonify(status="not found", message="challenge not found."), 404
    
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    teams: List[Team] = Team.query.all()
    
    response = {}
    for team in teams:
        services: List[Service] = db.session.execute(
            select(Service).where(
                and_(
                    Service.challenge_id == chall.id,
                    Service.team_id == team.id
                )
            )
        ).scalars().all()
        
        svcinfo = svcmodule.generator_public_services_info(team=team, challenge=chall, services=services)
        chall_data = response.get(chall.id, {})
        chall_data[team.id] = svcinfo
        response[chall.id] = chall_data

    return jsonify(status="success", data=response)
