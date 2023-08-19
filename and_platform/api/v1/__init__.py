from flask import Blueprint
from and_platform.api.v1.admin import adminapi_blueprint
from and_platform.api.v1.submission import submission_blueprint
from and_platform.api.v1.contest import public_contest_blueprint
from and_platform.api.v1.teams import public_teams_blueprint

apiv1_blueprint = Blueprint("apiv1", __name__, url_prefix="/v1")
apiv1_blueprint.register_blueprint(adminapi_blueprint)
apiv1_blueprint.register_blueprint(submission_blueprint)
apiv1_blueprint.register_blueprint(public_contest_blueprint)
apiv1_blueprint.register_blueprint(public_teams_blueprint)