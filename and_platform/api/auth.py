from flask import Blueprint, jsonify, request
from sqlalchemy import select
from werkzeug.security import check_password_hash

from and_platform.models import db, Teams


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.post("/login")
def login():
    name = request.form.get("name")
    password = request.form.get("password")

    team = db.session.execute(
        select(Teams).filter(Teams.name == name)
    ).scalar_one_or_none()
    if not team:
        return jsonify(False)

    return jsonify(check_password_hash(team.password, password))  # type: ignore
