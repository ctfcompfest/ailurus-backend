from ailurus.utils.config import get_config
from ailurus.models import Team
from flask import jsonify, request
from flask_jwt_extended import current_user, verify_jwt_in_request
from typing import Optional

current_team: Optional[Team] = current_user

def admin_only():
    # Preflight
    if request.method == "OPTIONS":
        return
    req_secret = request.headers.get("x-adce-secret", None)

    # If server admin forgot to set ADMIN_SECRET, all request to the admin API are forbid
    if get_config("ADMIN_SECRET") == None or req_secret != get_config("ADMIN_SECRET"):
        return jsonify(status="forbidden", message="forbidden."), 403

def validteam_only():
    # Preflight
    if request.method == "OPTIONS":
        return
    
    verify_jwt_in_request()
    if current_team == None:
        return jsonify(status="forbidden", message="forbidden."), 403
