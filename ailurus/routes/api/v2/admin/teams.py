from ailurus.models import db, Team, Challenge
from ailurus.schema import TeamSchema
from ailurus.utils.config import get_config
from ailurus.utils.svcmode import get_svcmode_module
from flask import Blueprint, jsonify, request
from marshmallow.exceptions import ValidationError
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

team_blueprint = Blueprint("team", __name__, url_prefix="/teams")
team_schema = TeamSchema()

@team_blueprint.get("/")
def get_all_teams():
    teams = Team.query.order_by(Team.id).all()
    return (
        jsonify(
            status="success",
            data=team_schema.dump(teams, many=True),
        ),
        200,
    )

@team_blueprint.post("/")
def create_bulk_teams():
    json_data = request.get_json()
    if not isinstance(json_data, list):
        return jsonify(status="failed", message='input data should be a list of teams.'), 400
    
    try:
        teams_data: List[Team] = team_schema.load(json_data, transient=True, many=True)
    except ValidationError:
        return jsonify(status="failed", message=f"missing data for required field."), 400

    teams_email: List[str] = [team.email for team in teams_data]
    if len(set(teams_email)) != len(teams_email):
        return jsonify(status="failed", message=f"e-mail duplication found."), 400

    server_email: Tuple[Team] | None = db.session.execute(
        select(Team).where(Team.email.in_(teams_email))
    ).first()
    if server_email is not None:
        return jsonify(status="failed", message=f"e-mail '{server_email[0].email}' has been registered."), 409
    
    db.session.add_all(teams_data)
    db.session.commit()

    return (
        jsonify(
            status="success",
            message="team registered",
            data=team_schema.dump(teams_data, many=True),
        ),
        200,
    )

@team_blueprint.get("/<int:team_id>/")
def get_team_detail(team_id):
    team = Team.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404
    return (
        jsonify(
            status="success",
            data=team_schema.dump(team),
        ),
        200,
    )


@team_blueprint.patch("/<int:team_id>/")
def update_team(team_id):
    team: Team | None = Team.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404

    json_data = request.get_json()
    _ = team_schema.load(json_data, transient=True, instance=team, partial=True)

    try:
        db.session.commit()
        db.session.refresh(team)
    except IntegrityError:
        db.session.rollback()
        return jsonify(status="failed", message=f"e-mail '{team.email}' has been registered."), 400

    return (
        jsonify(
            status="success",
            message="{} info successfully updated.".format(team.name),
            data=team_schema.dump(team),
        ),
        200,
    )

@team_blueprint.delete("/<int:team_id>/")
def delete_team(team_id):
    team = Team.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404

    team_name = team.name
    db.session.delete(team)
    db.session.commit()
    
    return (
        jsonify(
            status="success",
            message="{} successfully deleted.".format(team_name),
            data=team_schema.dump(team)
        ),
        200,
    )

@team_blueprint.route("/<int:team_id>/challenges/<int:challenge_id>/service-manager/", methods=["GET", "POST"])
def handle_service_manager(team_id, challenge_id):
    team = Team.query.filter_by(id=team_id).first()
    if team is None:
        return jsonify(status="not found", message="team not found"), 404
    
    chall: Challenge = Challenge.query.filter_by(id=challenge_id).first()
    if not chall:
        return jsonify(status="not found", message="challenge not found."), 404
    
    svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
    return svcmodule.handler_svcmanager_request(
        team_id=team.id,
        challenge_id=challenge_id,
        request=request,
        is_allow_manage=True,
        is_admin=True,
    )
