from and_platform.core.config import get_config
from and_platform.models import db, Teams
from flask import current_app as app, jsonify, request

import jwt

def admin_only():
    req_secret = request.headers.get("x-adce-secret", None)

    # If server admin forgot to set ADCE_SECRET, all request to the admin API are forbid
    if get_config("ADCE_SECRET") == None or req_secret != get_config("ADCE_SECRET"):
        return jsonify(status="forbidden", message="forbidden."), 403

def validteam_only():
    SECRET = app.config["SECRET_KEY"]
    req_auth = request.headers.get("authorization")
    if req_auth == None:
        return jsonify(status="forbidden", message="forbidden."), 403
    
    req_jwt = req_auth.split(" ")[-1]
    try:
        jwt_claim = jwt.decode(req_jwt, SECRET, algorithms=["HS512"])
        team = db.session.execute(
            Teams.__table__.select().where(Teams.id == jwt_claim["team"]["id"])
        ).fetchone()
        if team == None:
            return jsonify(status="forbidden", message="forbidden."), 403
    except:
        return jsonify(status="forbidden", message="forbidden."), 403