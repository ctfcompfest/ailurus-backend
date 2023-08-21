from sqlalchemy import select
from and_platform.api.helper import convert_model_to_dict
from and_platform.core.challenge import get_challenges_directory, load_challenge
from and_platform.core.config import get_config
from and_platform.models import Challenges, Servers, db
from flask import Blueprint, jsonify, request

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

        chall = Challenges.query.where(Challenges.id == chall_id).first()
        if chall == None:
            chall = Challenges(  # type: ignore
                id=int(chall_id)
            )
            db.session.add(chall)
        chall.name = chall_data["name"]
        chall.description = chall_data["description"]
        chall.num_expose = chall_data["num_expose"]

        if server_mode == "sharing" and chall_data.get("server_id"):
            server = db.session.execute(
                select(Servers).filter(Servers.id == chall_data["server_id"])
            ).scalar_one()
            chall.server_id = server.id
            chall.server_host = server.host
        
        populated_challs.append(chall)

    db.session.commit()
    populated_challs = Challenges.query.all()
    return (
        jsonify(status="success", data=convert_model_to_dict(populated_challs)),
        200,
    )
