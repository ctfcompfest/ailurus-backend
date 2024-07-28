from ailurus.models import db, Team
from ailurus.utils.security import validteam_only
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy import select
from werkzeug.security import check_password_hash
from flask_jwt_extended import verify_jwt_in_request

authenticate_blueprint = Blueprint(
    "authenticate_blueprint", __name__, url_prefix="/authenticate"
)

@authenticate_blueprint.post("/")
def login():
    email = request.json.get("email")
    password = request.json.get("password")
    if not email or not password:
        return jsonify(status="forbidden", message="email or password is wrong."), 403

    team = db.session.execute(
        select(Team).filter(Team.email == email)
    ).scalar_one_or_none()

    if team is not None and check_password_hash(team.password, password):
        access_token = create_access_token(
            identity={"team": {"id": team.id, "name": team.name}}
        )
        return jsonify(status="success", data=access_token), 200

    return jsonify(status="forbidden", message="email or password is wrong."), 403

@authenticate_blueprint.post("/token-check/")
def token_check():
    verify_jwt_in_request()
    return jsonify(status="success", message="token is valid.")