from and_platform.api.helper import convert_model_to_dict
from and_platform.models import Submissions
from flask import Blueprint, jsonify, request

submission_blueprint = Blueprint("submission", __name__, url_prefix="/submission")

@submission_blueprint.get('/')
def get_submission():
    DATA_PER_PAGE = 50
    ALLOWED_QUERY = ["team_id", "challenge_id", "round", "tick", "verdict"]

    page = request.args.get("page", 1, int)
    query_filter = []
    for elm in ALLOWED_QUERY:
        arg_val = request.args.get(elm, type=int)
        if not arg_val: continue
        query_filter.append(Submissions.__getattribute__(elm) == arg_val)
    
    submissions = Submissions.query.filter(**query_filter).paginate(page=page, per_page=DATA_PER_PAGE)
    response = {
        "submissions": convert_model_to_dict(submissions.item),
    }
    if submissions.has_next:
        response['next_page'] = submissions.next_num
    if submissions.has_prev:
        response['prev_page'] = submissions.prev_num
    
    return jsonify(status="success",data=response)