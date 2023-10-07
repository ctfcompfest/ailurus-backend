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
    is_freeze = freeze_time and datetime.now().astimezone() > freeze_time

    teams = Teams.query.all()
    scoreboard = []
    for team in teams:
        # TODO: REMOVE COMMENT
        #team_score = get_overall_team_score(team.id, freeze_time)
        team_score = get_overall_team_score(team.id)

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

    scoreboard_sort = sorted(scoreboard, key=lambda x: x["total_score"], reverse=True)
    scoreboard_sort[0]["rank"] = 1
    for i in range(1, len(scoreboard_sort)):
        scoreboard_sort[i]["rank"] = scoreboard_sort[i-1]["rank"]
        if scoreboard_sort[i]["total_score"] != scoreboard_sort[i-1]["total_score"]:
            scoreboard_sort[i]["rank"] += 1

    return jsonify(status="success", is_freeze=is_freeze, data=scoreboard_sort)
