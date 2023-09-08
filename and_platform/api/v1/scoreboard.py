from and_platform.cache import cache
from and_platform.models import Teams
from and_platform.core.config import get_config
from and_platform.core.score import get_overall_team_score
from flask import Blueprint, jsonify
from datetime import datetime

public_scoreboard_blueprint = Blueprint("public_scoreboard", __name__, url_prefix="/scoreboard")


@public_scoreboard_blueprint.get("/")
@cache.cached(timeout=60)
def get_public_scoreboard():
    freeze_time = get_config("FREEZE_TIME")
    freeze_time = freeze_time.replace(tzinfo=None)
    is_freeze = freeze_time and datetime.utcnow() > freeze_time

    teams = Teams.query.all()
    scoreboard = []
    for team in teams:
        team_score = get_overall_team_score(team.id, freeze_time)

        tmp_chall = {}
        for chall in team_score["challenges"]:
            chall_id = chall["challenge_id"]
            chall.pop("challenge_id")
            tmp_chall[chall_id] = chall

        team_score.pop("team_id")
        team_score.update({
            "id": team.id,
            "name": team.name,
            "challenges": tmp_chall
        })

        scoreboard.append(team_score)

    scoreboard_sort = sorted(scoreboard, key=lambda x: x["total_score"])
    for i in range(len(scoreboard_sort)):
        scoreboard_sort[i]["rank"] = i+1
    return jsonify(status="success", is_freeze=is_freeze, data=scoreboard_sort)