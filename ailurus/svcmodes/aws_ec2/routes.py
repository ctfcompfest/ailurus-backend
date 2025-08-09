from ailurus.models import db
from ailurus.utils.config import get_config
from ailurus.utils.security import svcmode_match_only
from flask import Blueprint, request, jsonify

from .models import CheckerAgentReport

import json
import jwt
import logging

log = logging.getLogger(__name__)

checker_agent_blueprint = Blueprint("awsec2_checker_agent", __name__, url_prefix="/api/v2/checkeragent")
checker_agent_blueprint.before_request(svcmode_match_only("aws_ec2"))

@checker_agent_blueprint.post("/")
def receive_checker_agent_report():
    if 'X-Forwarded-For' in request.headers:
        source_ip = request.headers.getlist('X-Forwarded-For')[0]
    else:
        source_ip = request.remote_addr
    request_data = request.get_json().get("data")
    if not request_data:
        return jsonify(status="failed", message="missing required field.")

    try:
        claim = jwt.decode(request_data, get_config("CHECKER_AGENT_SECRET"), algorithms="HS256", leeway=5, options={"verify_iat": True, "verify_signature": True})
        
        report = CheckerAgentReport(
            ip_source=source_ip,
            selinux_status=claim["selinux"],
            flag_status=json.dumps(claim["flag"]),
            challenge_status=json.dumps(claim["challs"]),
        )
        db.session.add(report)
        db.session.commit()

        return jsonify(status="success")
    except jwt.InvalidSignatureError:
        log.error("invalid signature")
        return jsonify(status="failed", message="Invalid signature."), 400
    except jwt.InvalidIssuedAtError:
        log.error("token expired because iat")
        return jsonify(status="failed", message="Token has expired."), 400
    except jwt.ExpiredSignatureError:
        log.error("token expired because expired signature")
        return jsonify(status="failed", message="Token has expired."), 400
    except Exception as e:
        log.error(e)
        return jsonify(status="failed", message="invalid token."), 400