from ailurus.models import db, Service, Challenge, Team
from ailurus.schema import ServiceSchema
from ailurus.utils.config import _convert_config_value, get_config
from ailurus.utils.svcmode import get_svcmode_module
from flask import Blueprint, jsonify, request
from typing import List, Tuple

import itertools

service_blueprint = Blueprint("service", __name__)
service_schema = ServiceSchema()

@service_blueprint.get("/services/")
def get_services():
    DATA_PER_PAGE = 50
    page = request.args.get("page", 1, int)
    ALLOWED_QUERY = ["team_id", "challenge_id"]
    
    query_filter = []
    for elm in ALLOWED_QUERY:
        arg_val = request.args.get(elm, type=_convert_config_value)
        if arg_val == None: continue
        query_filter.append(getattr(Service, elm) == arg_val)
    
    services: List[Tuple[Service, str, str]] = db.session.query(
            Service,
            Challenge.title,
            Team.name
        ).join(Challenge,
            Challenge.id == Service.challenge_id
        ).join(Team,
            Team.id == Service.team_id
        ).filter(*query_filter).order_by(Service.id.desc()).paginate(page=page, per_page=DATA_PER_PAGE)

    services_data = []
    for data in services:
        service, chall_name, team_name = data
        services_data.append({
            "challenge_name": chall_name,
            "team_name": team_name,
            **service_schema.dump(service)
        })
    
    pagination_resp = {
        "current_page": page,
    }
    if services.has_next:
        pagination_resp['next_page'] = services.next_num
    if services.has_prev:
        pagination_resp['prev_page'] = services.prev_num

    return jsonify(status="success", data=services_data, **pagination_resp)

@service_blueprint.post("/services-manager/")
def handle_services_manager():
    request_data = request.get_json()
    if "challenges" not in request_data or "teams" not in request_data:
        return jsonify(status="error", message="Missing 'challenges' or 'teams' field in request"), 400

    if request_data["challenges"] == "*":
        challs: List[Challenge] = Challenge.query.all()
    else:
        challs = Challenge.query.filter(Challenge.id.in_(request_data["challenges"])).all()
        if len(challs) != len(request_data["challenges"]):
            return jsonify(status="error", message="some challenge not found."), 400

    if request_data["teams"] == "*":
        teams: List[Team] = Team.query.all()
    else:
        teams = Team.query.filter(Team.id.in_(request_data["teams"])).all()
        if len(teams) != len(request_data["teams"]):
            return jsonify(status="error", message="some team not found."), 400
        
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    for team, chall in itertools.product(teams, challs):
        svcmodule.handler_svcmanager_request(
            team_id=team.id,
            challenge_id=chall.id,
            request=request,
            is_allow_manage=True,
            is_admin=True,
        )

    return jsonify(status="success", message="provisioning successfully scheduled.")

@service_blueprint.route("/teams/<int:team_id>/challenges/<int:challenge_id>/service-manager/", methods=["GET", "POST"])
def handle_service_manager(team_id, challenge_id):
    team = Team.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404
    
    chall: Challenge = Challenge.query.filter_by(id=challenge_id).first()
    if not chall:
        return jsonify(status="not found", message="challenge not found."), 404
    
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    return svcmodule.handler_svcmanager_request(
        team_id=team.id,
        challenge_id=challenge_id,
        request=request,
        is_allow_manage=True,
        is_admin=True,
    )
