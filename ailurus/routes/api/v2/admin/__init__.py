from flask import Blueprint
from ailurus.routes.api.v2.admin.teams import teams_blueprint
from ailurus.routes.api.v2.admin.services import service_blueprint
from ailurus.routes.api.v2.admin.submissions import submission_blueprint
from ailurus.utils.security import admin_only

adminapi_blueprint = Blueprint("admin", __name__, url_prefix="/admin")
adminapi_blueprint.before_request(admin_only)
adminapi_blueprint.register_blueprint(teams_blueprint)
adminapi_blueprint.register_blueprint(service_blueprint)
adminapi_blueprint.register_blueprint(submission_blueprint)
