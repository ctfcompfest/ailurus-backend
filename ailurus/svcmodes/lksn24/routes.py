from ailurus.models import db
from ailurus.utils.config import get_config
from ailurus.utils.security import svcmode_match_only
from flask import Blueprint, request, jsonify

from .models import CheckerAgentReport

import json
import jwt

checker_agent_blueprint = Blueprint("checker_agent", __name__, url_prefix="/api/v2/checkeragent")
checker_agent_blueprint.before_request(svcmode_match_only("lksn24"))

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
            source_ip=source_ip,
            selinux_status=claim["selinux"],
            flag_status=json.dumps(claim["flag"]),
            challenge_status=json.dumps(claim["chall"]),
        )
        db.session.add(report)
        db.session.commit()

        return jsonify(status="success")
    except jwt.InvalidSignatureError:
        return jsonify(status="failed", message="Invalid signature."), 400
    except jwt.InvalidIssuedAtError:
        return jsonify(status="failed", message="Token has expired."), 400
    except jwt.ExpiredSignatureError:
        return jsonify(status="failed", message="Token has expired."), 400
    except Exception:
        return jsonify(status="failed", message="invalid token."), 400