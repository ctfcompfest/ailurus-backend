from flask import Blueprint
from and_platform.api.v1.admin import adminapi_blueprint

apiv1_blueprint = Blueprint("apiv1", __name__, url_prefix="/v1")
apiv1_blueprint.register_blueprint(adminapi_blueprint)