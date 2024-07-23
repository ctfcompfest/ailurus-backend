from flask import Blueprint
from ailurus.routes.api.v2.admin import adminapi_blueprint

apiv2_blueprint = Blueprint("apiv2", __name__, url_prefix="/v2")
apiv2_blueprint.register_blueprint(adminapi_blueprint)