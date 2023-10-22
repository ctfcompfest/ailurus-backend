from flask import Blueprint
from and_platform.core.security import gateflag_only

flagserverapi_blueprint = Blueprint("flagserver", __name__, url_prefix="/flagserver")
flagserverapi_blueprint.before_request(gateflag_only)

@flagserverapi_blueprint.post("/user_flag")
def user_flag():
    pass

@flagserverapi_blueprint.post("/root_flag")
def root_flag():
    pass