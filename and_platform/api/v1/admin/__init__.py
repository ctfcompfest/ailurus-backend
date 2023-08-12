from flask import Blueprint
from and_platform.api.v1.admin.contest import contest_blueprint
from and_platform.core.security import admin_only

adminapi_blueprint = Blueprint("admin", __name__, url_prefix="/admin", )
adminapi_blueprint.before_request(admin_only)
adminapi_blueprint.register_blueprint(contest_blueprint)

