from ailurus.models import db, Challenge, ChallengeRelease, CheckerResult, CheckerStatus, Team, Service
from ailurus.utils.config import get_config, is_defense_phased
from ailurus.utils.security import validteam_only
from ailurus.utils.svcmode import get_svcmode_module
from ailurus.utils.cache import cache
from flask import Blueprint, jsonify
from sqlalchemy import and_, select, func
from typing import List, Tuple, Any

import itertools
import json

__all__ = ["public_services_blueprint", "auth_services_blueprint"]

public_services_blueprint = Blueprint("public_services", __name__)

@public_services_blueprint.get("/services-status/")
@cache.cached(timeout=30)
def get_all_services_status():
    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    chall_release = ChallengeRelease.get_all_released_challenges(current_round)

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))

    latest_id = func.max(CheckerResult.id).label("latest_id")
    checker_results: List[Tuple[int, int, int, CheckerStatus, str]] = db.session.query(
        latest_id,
        CheckerResult.challenge_id,
        CheckerResult.team_id,
        CheckerResult.status,
        CheckerResult.detail,
    ).where(
        CheckerResult.challenge_id.in_(chall_release),
        CheckerResult.status.in_([
            CheckerStatus.FAULTY,
            CheckerStatus.VALID,
        ])
    ).group_by(
        CheckerResult.challenge_id,
        CheckerResult.team_id,
        CheckerResult.status,
        CheckerResult.detail,
    ).order_by(latest_id.desc()).all()
    
    response = {}
    for _, challenge_id, team_id, status, detail in checker_results:
        chall_data = response.get(challenge_id, {})
        if team_id in chall_data: continue

        chall_data[team_id] = {
            "status": status.value,
            "detail": svcmode.generator_public_services_status_detail(json.loads(detail)),
        }
        response[challenge_id] = chall_data

    return jsonify(status="success", data=response)


@public_services_blueprint.get("/teams/<int:team_id>/services-status/")
@cache.cached(timeout=30)
def get_all_services_status_from_team(team_id):
    team = Team.query.filter_by(id=team_id).first()
    if not team:
        return jsonify(status="not found.", message="team not found."), 404

    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
        
    chall_release = ChallengeRelease.get_challenges_from_round(current_round)

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    latest_id = func.max(CheckerResult.id).label("latest_id")
    checker_results: List[Tuple[int, int, CheckerStatus, str]] = db.session.query(
        latest_id,
        CheckerResult.challenge_id,
        CheckerResult.status,
        CheckerResult.detail,
    ).where(
        CheckerResult.team_id == team_id,
        CheckerResult.challenge_id.in_(chall_release),
        CheckerResult.status.in_([
            CheckerStatus.FAULTY,
            CheckerStatus.VALID,
        ])
    ).group_by(
        CheckerResult.challenge_id,
        CheckerResult.team_id,
        CheckerResult.status,
        CheckerResult.detail,
    ).order_by(latest_id.desc()).all()
    
    response = {}
    for _, challenge_id, status, detail in checker_results:
        if challenge_id in response: continue
        response[challenge_id] = {
            "status": status.value,
            "detail": svcmode.generator_public_services_status_detail(json.loads(detail)),
        }

    return jsonify(status="success", data=response)


@public_services_blueprint.get("/challenges/<int:challenge_id>/services-status/")
@cache.cached(timeout=30)
def get_all_services_status_from_challenge(challenge_id):
    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
        
    chall_release = ChallengeRelease.get_challenges_from_round(current_round)

    if challenge_id not in chall_release:
        return jsonify(status="not found.", message="challenge not found."), 404

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))
    latest_id = func.max(CheckerResult.id).label("latest_id")
    checker_results: List[Tuple[int, int, CheckerStatus, str]] = db.session.query(
        latest_id,
        CheckerResult.team_id,
        CheckerResult.status,
        CheckerResult.detail,
    ).where(
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
    ).order_by(latest_id.desc()).all()
    
    response = {}
    for _, team_id, status, detail in checker_results:
        if team_id in response: continue
        response[team_id] = {
            "status": status.value,
            "detail": svcmode.generator_public_services_status_detail(json.loads(detail)),
        }

    return jsonify(status="success", data=response)


@public_services_blueprint.get("/teams/<int:team_id>/challenges/<int:challenge_id>/services-status/")
@cache.cached(timeout=30)
def get_all_services_status_from_team_and_chall(team_id, challenge_id):
    team = Team.query.filter_by(id=team_id).first()
    if not team:
        return jsonify(status="not found.", message="team not found."), 404

    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
        
    chall_release = ChallengeRelease.get_challenges_from_round(current_round)
    if challenge_id not in chall_release:
        return jsonify(status="not found.", message="challenge not found."), 404

    svcmode = get_svcmode_module(get_config("SERVICE_MODE"))

    latest_id = func.max(CheckerResult.id).label("latest_id")
    checker_result: Tuple[int, CheckerStatus, str] | None = db.session.query(
        latest_id,
        CheckerResult.status,
        CheckerResult.detail,
    ).where(
        CheckerResult.team_id == team_id,
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


auth_services_blueprint = Blueprint("auth_services", __name__)
auth_services_blueprint.before_request(validteam_only)

@auth_services_blueprint.get("/services/")
@cache.cached(timeout=60)
def get_all_services():
    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    release_challs: List[Challenge] = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(ChallengeRelease.round == current_round)
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

@auth_services_blueprint.get("/teams/<int:team_id>/services/")
@cache.cached(timeout=60)
def get_all_services_from_team(team_id):
    team: Team = Team.query.filter_by(id=team_id).first()
    if not team:
        return jsonify(status="not found", message="team not found."), 404
    
    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    release_challs: List[Challenge] = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(ChallengeRelease.round == current_round)
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
        response[chall.id] = svcinfo

    return jsonify(status="success", data=response)


@auth_services_blueprint.get("/challenges/<int:challenge_id>/services/")
@cache.cached(timeout=60)
def get_all_services_from_challenge(challenge_id):
    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    chall: Challenge = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(
                ChallengeRelease.round == current_round,
                Challenge.id == challenge_id
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
        response[team.id] = svcinfo

    return jsonify(status="success", data=response)


@auth_services_blueprint.get("/teams/<int:team_id>/challenges/<int:challenge_id>/services/")
@cache.cached(timeout=60)
def get_all_services_from_team_and_chall(team_id, challenge_id):
    team: Team = Team.query.filter_by(id=team_id).first()
    if not team:
        return jsonify(status="not found", message="team not found."), 404
    
    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    chall: Challenge = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id,
            ).where(
                ChallengeRelease.round == current_round,
                Challenge.id == challenge_id,
            )
        ).scalars().first()
    if not chall:
        return jsonify(status="not found", message="challenge not found."), 404
    
    services: List[Service] = db.session.execute(
        select(Service).where(
            and_(
                Service.challenge_id == challenge_id,
                Service.team_id == team_id
            )
        )
    ).scalars().all()
        
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    svcinfo = svcmodule.generator_public_services_info(team=team, challenge=chall, services=services)
    return jsonify(status="success", data=svcinfo)

