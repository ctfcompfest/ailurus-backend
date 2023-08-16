from and_platform.models import db, Challenges, Teams, Services
from and_platform.core.config import get_config
from and_platform.core.service import do_provision_private_mode, do_provision_sharing_mode
from flask import Blueprint, jsonify, request, views
from itertools import product

service_blueprint = Blueprint("service", __name__, url_prefix="/services")

class ServiceProvision(views.MethodView):
    def post(self):
        req = request.get_json()
        provision_challs = req.get("challenges")
        provision_teams = req.get("teams")
        if not provision_challs or not provision_teams:
            return jsonify(status="failed", message="invalid body."), 400
        
        teams_query = Teams.__table__.select()
        challs_query = Challenges.__table__.select()
        if isinstance(provision_teams, list):
            teams_query = teams_query.where(Teams.id.in_(provision_teams))
        if isinstance(provision_challs, list):
            challs_query = challs_query.where(Challenges.id.in_(provision_challs))
        
        teams = db.session.execute(teams_query).all()
        challenges = db.session.execute(challs_query).all()
        if (isinstance(provision_teams, list) and len(teams) != len(provision_teams)) \
            or (isinstance(provision_challs, list) and len(challenges) != len(provision_challs)):
            return jsonify(status="failed", message="challenge or team cannot be found."), 400
        
        try:
            if get_config("SERVER_MODE") == "private":
                for team in teams:
                    do_provision_private_mode(team, challenges, team.server)
            if get_config("SERVER_MODE") == "sharing":
                for chall in challenges:
                    do_provision_sharing_mode(chall, teams, chall.server)
        except Exception as e:
            return jsonify(status="failed", message=e), 500
        return jsonify(status="success", message="successfully provision all requested services.")

service_blueprint.add_url_rule('/provision', view_func=ServiceProvision.as_view('service_provision'))