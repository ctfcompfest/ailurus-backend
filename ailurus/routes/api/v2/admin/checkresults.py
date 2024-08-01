from ailurus.models import db, CheckerResult, CheckerStatus, Challenge, Team
from ailurus.schema import CheckerResultSchema
from ailurus.utils.config import _convert_config_value
from flask import Blueprint, jsonify, request
from typing import List, Tuple

checkres_blueprint = Blueprint("checkresult", __name__, url_prefix="/checkresults")
checkres_schema = CheckerResultSchema()

@checkres_blueprint.get('/')
def get_submissions():
    DATA_PER_PAGE = 50
    ALLOWED_QUERY = ["team_id", "challenge_id", "round", "tick", "status"]

    page = request.args.get("page", 1, int)
    query_filter = []
    for elm in ALLOWED_QUERY:
        arg_val = request.args.get(elm, type=_convert_config_value)
        if arg_val == None: continue
        if elm == "status":
            arg_val = CheckerStatus(arg_val)
        query_filter.append(getattr(CheckerResult, elm) == arg_val)

    checkresults: List[Tuple[CheckerResult, str, str]] = db.session.query(
            CheckerResult,
            Challenge.title,
            Team.name
        ).join(Challenge,
            Challenge.id == CheckerResult.challenge_id
        ).join(Team,
            Team.id == CheckerResult.team_id
        ).filter(*query_filter).order_by(CheckerResult.id.desc()).paginate(page=page, per_page=DATA_PER_PAGE)
    
    checkres_datas = []
    for data in checkresults:
        checkerresult, chall_name, team_name = data
        checkres_datas.append({
            "challenge_name": chall_name,
            "team_name": team_name,
            **checkres_schema.dump(checkerresult)
        })
    
    pagination_resp = {
        "current_page": page,
    }
    if checkresults.has_next:
        pagination_resp['next_page'] = checkresults.next_num
    if checkresults.has_prev:
        pagination_resp['prev_page'] = checkresults.prev_num
    
    return jsonify(status="success",data=checkres_datas,**pagination_resp)