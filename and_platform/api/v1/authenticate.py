from and_platform.core.config import get_config
from flask import Blueprint, jsonify, request
from sqlalchemy import select
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

from and_platform.models import db, Teams

authenticate_blueprint = Blueprint(
    "authenticate_blueprint", __name__, url_prefix="/authenticate"
)


@authenticate_blueprint.route("/", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")

    team = db.session.execute(
        select(Teams).filter(Teams.email == email)
    ).scalar_one_or_none()

    if team is not None and check_password_hash(team.password, password):
        access_token = create_access_token(
            identity={"team": {"id": team.id, "name": team.name}}
        )
        return jsonify(status="success", data=access_token), 200

    return jsonify(status="forbidden", message="email or password is wrong."), 403
