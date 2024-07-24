from flask import Blueprint
from ailurus.routes.api.v2.admin.checkresults import checkres_blueprint
from ailurus.routes.api.v2.admin.configs import config_blueprint
from ailurus.routes.api.v2.admin.teams import teams_blueprint
from ailurus.routes.api.v2.admin.machines import machine_blueprint
from ailurus.routes.api.v2.admin.services import service_blueprint
from ailurus.routes.api.v2.admin.submissions import submission_blueprint
from ailurus.utils.security import admin_only

adminapi_blueprint = Blueprint("admin", __name__, url_prefix="/admin")
adminapi_blueprint.before_request(admin_only)
adminapi_blueprint.register_blueprint(checkres_blueprint)
adminapi_blueprint.register_blueprint(config_blueprint)
adminapi_blueprint.register_blueprint(machine_blueprint)
adminapi_blueprint.register_blueprint(service_blueprint)
adminapi_blueprint.register_blueprint(submission_blueprint)
adminapi_blueprint.register_blueprint(teams_blueprint)
