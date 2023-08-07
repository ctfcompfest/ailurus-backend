from flask import Blueprint


bp = Blueprint('flag', __name__, url_prefix='/flag')

@bp.get("/")
def hello_world():
    return "Hello world!"
