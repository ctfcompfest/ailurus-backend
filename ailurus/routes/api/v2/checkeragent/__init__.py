from ailurus.utils.security import checkeragent_only
from ailurus.models import db, CheckerAgentReport, Challenge
from flask import Blueprint, jsonify, request

import json

checkeragent_blueprint = Blueprint("checkeragent", __name__, url_prefix="checkeragent")
checkeragent_blueprint.before_request(checkeragent_only)

@checkeragent_blueprint.post("/")
def receive_checkeragent_report():
    data = request.get_json()
    if not data:
        return jsonify(error="No data provided"), 400
    if 'X-Forwarded-For' in request.headers:
        source_ip = request.headers.getlist('X-Forwarded-For')[0]
    else:
        source_ip = request.remote_addr

    chall: Challenge = Challenge.query.filter_by(slug=data["challenge_slug"]).first()
    agent_report = CheckerAgentReport(
        team_id=data["team_id"],
        challenge_id=chall.id,
        report=json.dumps(data["report"]),
        source_ip=source_ip
    )
    db.session.add(agent_report)
    db.session.commit()
    return jsonify(status="success")