from typing import Optional
from and_platform.core.config import get_config
from and_platform.models import db, Teams
from flask import jsonify, request
from flask_jwt_extended import current_user, verify_jwt_in_request

current_team: Optional[Teams] = current_user


def admin_only():
    # Preflight
    if request.method == "OPTIONS":
        return

    req_secret = request.headers.get("x-adce-secret", None)

    # If server admin forgot to set ADCE_SECRET, all request to the admin API are forbid
    if get_config("ADCE_SECRET") == None or req_secret != get_config("ADCE_SECRET"):
        return jsonify(status="forbidden", message="forbidden."), 403


def validteam_only():
    # Preflight
    if request.method == "OPTIONS":
        return
    
    verify_jwt_in_request()
    if current_team == None:
        return jsonify(status="forbidden", message="forbidden."), 403
