from pathlib import Path
from typing import TypedDict
from and_platform.api.helper import convert_model_to_dict
from and_platform.core.challenge import get_challenges_directory, load_challenge
from and_platform.core.config import get_config
from and_platform.models import Challenges, Services, Teams, db, Configs
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import select
import yaml

challenges_blueprint = Blueprint("challenges", __name__, url_prefix="/challenges")


@challenges_blueprint.post("/populate")
def populate_challenges():
    confirm_data: dict = request.get_json()
    if not confirm_data.get("confirm"):
        return jsonify(status="bad request", message="action not confirmed"), 400

    server_mode = get_config("SERVER_MODE")
    chall_dir = get_challenges_directory()
    populated_challs: list[Challenges] = []
    for path in chall_dir.iterdir():
        if not path.is_dir() or not path.name.startswith("chall-"):
            continue

        chall_id = path.name[6:]
        chall_data = load_challenge(chall_id)
        for team in db.session.execute(select(Teams)).scalars():
            chall = Challenges(  # type: ignore
                name=chall_data["title"],
                description=chall_data["description"],
                num_expose=chall_data["num_expose"],
            )

            if server_mode == "sharing":
                chall.server_id = team.server_id
                chall.server_host = team.server_host

            populated_challs.append(chall)

    db.session.add_all(populated_challs)
    db.session.commit()
    return (
        jsonify(status="success", data=convert_model_to_dict(populate_challenges)),
        200,
    )
