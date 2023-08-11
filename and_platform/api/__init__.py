from flask import Blueprint
from and_platform.api.v1 import apiv1_blueprint

api_blueprint = Blueprint("api", __name__, url_prefix="/api")
api_blueprint.register_blueprint(apiv1_blueprint)
