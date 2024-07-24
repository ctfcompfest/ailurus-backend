from ailurus.models import db, Service, Challenge, Team
from ailurus.schema import ServiceSchema
from flask import Blueprint, jsonify, request
from typing import List, Tuple

service_blueprint = Blueprint("service", __name__, url_prefix="/services")
service_schema = ServiceSchema()

@service_blueprint.get("/")
def get_services():
    DATA_PER_PAGE = 50
    page = request.args.get("page", 1, int)

    services: List[Tuple[Service, str, str]] = db.session.query(
            Service,
            Challenge.title,
            Team.name
        ).join(Challenge,
            Challenge.id == Service.challenge_id
        ).join(Team,
            Team.id == Service.team_id
        ).order_by(Service.id.desc()).paginate(page=page, per_page=DATA_PER_PAGE)

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