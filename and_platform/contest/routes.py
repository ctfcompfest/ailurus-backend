from flask import Blueprint


bp = Blueprint('contest', __name__, url_prefix='/contest')

@bp.get("/")
def hello_world():
    return "Hello world!"
