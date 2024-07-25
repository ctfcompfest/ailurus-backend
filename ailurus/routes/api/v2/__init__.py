from flask import Blueprint
from ailurus.routes.api.v2.admin import adminapi_blueprint
from ailurus.routes.api.v2.authenticate import authenticate_blueprint
from ailurus.routes.api.v2.challenges import public_challenge_blueprint

apiv2_blueprint = Blueprint("apiv2", __name__, url_prefix="/v2")
apiv2_blueprint.register_blueprint(adminapi_blueprint)
apiv2_blueprint.register_blueprint(authenticate_blueprint)
apiv2_blueprint.register_blueprint(public_challenge_blueprint)