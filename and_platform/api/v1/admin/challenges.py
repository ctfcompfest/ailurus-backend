from sqlalchemy import select
from and_platform.api.helper import convert_model_to_dict
from and_platform.core.challenge import (
    ChallengeData,
    get_challenges_directory,
    load_challenge,
)
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
        chall = Challenges(  # type: ignore
            id=int(chall_id),
            name=chall_data["name"],
            description=chall_data["description"],
            num_expose=chall_data["num_expose"],
        )

        if server_mode == "sharing" and chall_data.get("server_id"):
            server = db.session.execute(
                select(Servers).filter(Servers.id == chall_data["server_id"])
            ).scalar_one()
            chall.server_id = server.id
            chall.server_host = server.host

        populated_challs.append(chall)

    db.session.add_all(populated_challs)
    db.session.commit()
    return (
        jsonify(status="success", data=convert_model_to_dict(populated_challs)),
        200,
    )


@challenges_blueprint.get("/")
def get_all_challs():
    challenges = db.session.execute(select(Challenges)).scalars()
    return (
        jsonify(
            status="success",
            data=convert_model_to_dict(challenges),
        ),
        200,
    )


@challenges_blueprint.post("/")
def create_new_chall():
    server_mode = get_config("SERVER_MODE")
    data: ChallengeData = request.get_json()

    name = data.get("name")
    description = data.get("description")
    num_expose = data.get("num_expose")
    server_id = data.get("server_id")

    if not (name and description and num_expose) or (
        server_mode == "sharing" and not server_id
    ):
        return jsonify(status="failed", message="missing required attributes"), 400

    chall = Challenges(
        name=name,
        description=description,
        num_expose=num_expose,
    )

    if server_mode == "sharing":
        server = db.session.execute(
            select(Servers).filter(Servers.id == server_id)
        ).scalar_one()
        chall.server_id = server.id
        chall.server_host = server.host

    db.sesion.add(chall)
    db.session.commit()
    return jsonify(status="success", data=convert_model_to_dict(chall))


@challenges_blueprint.get("/<int:challenge_id>")
def get_chall(challenge_id: int):
    chall = db.session.get(Challenges, challenge_id)
    if not chall:
        return jsonify(status="not found", message="challenge not found"), 404

    return jsonify(status="success", data=convert_model_to_dict(chall))


@challenges_blueprint.post("/<int:challenge_id>")
def update_chall(challenge_id: int):
    server_mode = get_config("SERVER_MODE")
    data: ChallengeData = request.get_json()

    chall = db.session.get(Challenges, challenge_id)
    if not chall:
        return jsonify(status="not found", message="challenge not found"), 404

    chall.name = data.get("name", chall.name)
    chall.description = data.get("description", chall.description)
    chall.num_expose = data.get("num_expose", chall.num_expose)
    server_id = data.get("server_id", chall.server_id)

    if server_mode == "sharing":
        server = db.session.execute(
            select(Servers).filter(Servers.id == server_id)
        ).scalar_one()
        chall.server_id = server.id
        chall.server_host = server.host

    db.session.commit()
    return jsonify(status="success", data=convert_model_to_dict(chall))


@challenges_blueprint.delete("/<int:challenge_id>")
def delete_chall(challenge_id: int):
    chall = db.session.get(Challenges, challenge_id)
    if not chall:
        return jsonify(status="not found", message="challenge not found"), 404

    db.session.delete(chall)
    db.session.commit()
    return jsonify(status="success", message=f"challenge {challenge_id} deleted")
