from and_platform.models import db, Challenges, Teams, Services
from and_platform.core.config import get_config
from and_platform.core.service import do_provision
from flask import Blueprint, jsonify, request, views, current_app as app

service_blueprint = Blueprint("service", __name__, url_prefix="/services")

class ServiceProvision(views.MethodView):
    def post(self):
        req = request.get_json()
        provision_challs = req.get("challenges")
        provision_teams = req.get("teams")
        if not provision_challs or not provision_teams:
            return jsonify(status="failed", message="invalid body."), 400
        
        teams_query = Teams.query
        challs_query = Challenges.query
        if isinstance(provision_teams, list):
            teams_query = teams_query.where(Teams.id.in_(provision_teams))
        if isinstance(provision_challs, list):
            challs_query = challs_query.where(Challenges.id.in_(provision_challs))
        
        teams = teams_query.all()
        challenges = challs_query.all()
        if (isinstance(provision_teams, list) and len(teams) != len(provision_teams)) \
            or (isinstance(provision_challs, list) and len(challenges) != len(provision_challs)):
            return jsonify(status="failed", message="challenge or team cannot be found."), 400
        
        server_mode = get_config("SERVER_MODE")
        for team in teams:
            for chall in challenges:
                if Services.is_teamservice_exist(team.id, chall.id): continue
                if server_mode == "private": server = team.server
                else: server = chall.server
                
                try:
                    services = do_provision(team, chall, server)
                except Exception as ex:
                    error_msg = f"error when provisioning challenge id={chall.id} for team id={team.id}: {ex}"
                    app.logger.error(ex, exc_info=True)
                    return jsonify(status="failed", message=error_msg), 500

                db.session.add_all(services)
                db.session.commit()
        
        return jsonify(status="success", message="successfully provision all requested services.")

service_blueprint.add_url_rule('/provision', view_func=ServiceProvision.as_view('service_provision'))