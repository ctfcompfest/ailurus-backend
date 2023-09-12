from and_platform.api.helper import convert_model_to_dict
from and_platform.models import CheckerQueues
from flask import Blueprint, jsonify, request
from flask_sqlalchemy.pagination import Pagination

checker_blueprint = Blueprint("checker", __name__, url_prefix="/checker")

@checker_blueprint.get('/')
def get_checker_result():
    DATA_PER_PAGE = 50
    ALLOWED_QUERY = ["team_id", "challenge_id", "round", "tick"]

    page = request.args.get("page", 1, int)
    query_filter = []
    for elm in ALLOWED_QUERY:
        arg_val = request.args.get(elm, int)
        if not arg_val: continue
        query_filter.append(CheckerQueues.__getattribute__(elm) == arg_val)
    
    checker_results = CheckerQueues.query.filter(**query_filter).paginate(page=page, per_page=DATA_PER_PAGE)
    response = {
        "checkers": convert_model_to_dict(checker_results.item),
    }
    if checker_results.has_next:
        response['next_page'] = checker_results.next_num
    if checker_results.has_prev:
        response['prev_page'] = checker_results.prev_num
    
    return jsonify(status="success",data=response)