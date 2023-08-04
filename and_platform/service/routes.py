from flask import Blueprint


bp = Blueprint('service', __name__, url_prefix='/service')

@bp.get("/")
def hello_world():
    return "Hello world!"
