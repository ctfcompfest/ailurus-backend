from flask import Blueprint
from ailurus.routes.api.v2 import apiv2_blueprint

api_blueprint = Blueprint("api", __name__, url_prefix="/api")
api_blueprint.register_blueprint(apiv2_blueprint)

@api_blueprint.get('/ping/')
def ping():
    return 'pong'