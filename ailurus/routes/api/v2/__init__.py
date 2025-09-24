from flask import Blueprint
from ailurus.routes.api.v2.admin import adminapi_blueprint
from ailurus.routes.api.v2.authenticate import authenticate_blueprint
from ailurus.routes.api.v2.challenges import public_challenge_blueprint
from ailurus.routes.api.v2.contest import contestinfo_blueprint
from ailurus.routes.api.v2.docs import public_docs_blueprint
from ailurus.routes.api.v2.leaderboard import public_leaderboard_blueprint
from ailurus.routes.api.v2.my import myapi_blueprint
from ailurus.routes.api.v2.submit import submit_blueprint
from ailurus.routes.api.v2.teams import public_team_blueprint
from ailurus.routes.api.v2.worker import worker_blueprint
from ailurus.routes.api.v2.services import auth_services_blueprint, public_services_blueprint

apiv2_blueprint = Blueprint("apiv2", __name__, url_prefix="/v2")
apiv2_blueprint.register_blueprint(adminapi_blueprint)
apiv2_blueprint.register_blueprint(auth_services_blueprint)
apiv2_blueprint.register_blueprint(authenticate_blueprint)
apiv2_blueprint.register_blueprint(contestinfo_blueprint)
apiv2_blueprint.register_blueprint(myapi_blueprint)
apiv2_blueprint.register_blueprint(public_challenge_blueprint)
apiv2_blueprint.register_blueprint(public_docs_blueprint)
apiv2_blueprint.register_blueprint(public_leaderboard_blueprint)
apiv2_blueprint.register_blueprint(public_services_blueprint)
apiv2_blueprint.register_blueprint(public_team_blueprint)
apiv2_blueprint.register_blueprint(submit_blueprint)
apiv2_blueprint.register_blueprint(worker_blueprint)
