from and_platform.api.helper import convert_model_to_dict
from and_platform.models import db, Submissions, Challenges, Teams
from flask import Blueprint, jsonify, request
from and_platform.core.config import _convert_config_value

submission_blueprint = Blueprint("submission", __name__, url_prefix="/submission")

@submission_blueprint.get('/')
def get_submission():
    DATA_PER_PAGE = 50
    ALLOWED_QUERY = ["team_id", "challenge_id", "round", "tick", "verdict"]

    page = request.args.get("page", 1, int)
    query_filter = []
    for elm in ALLOWED_QUERY:
        arg_val = request.args.get(elm, type=_convert_config_value)
        if arg_val == None: continue
        query_filter.append(getattr(Submissions, elm) == arg_val)

    submissions = db.session.query(
            Submissions,
            Challenges.name,
            Teams.name,
        ).join(Challenges,
            Challenges.id == Submissions.challenge_id
        ).join(Teams,
            Teams.id == Submissions.team_id
        ).filter(*query_filter).order_by(Submissions.id.desc()).paginate(page=page, per_page=DATA_PER_PAGE)
    
    submissions_data = []
    for data in submissions.items:
        submission, chall_name, team_name = data
        submissions_data.append({
            "challenge_name": chall_name,
            "team_name": team_name,
            **convert_model_to_dict(submission)
        })
    
    response = {
        "submissions": submissions_data,
        "current_page": page,
    }

    if submissions.has_next:
        response['next_page'] = submissions.next_num
    if submissions.has_prev:
        response['prev_page'] = submissions.prev_num
    
    return jsonify(status="success",data=response)