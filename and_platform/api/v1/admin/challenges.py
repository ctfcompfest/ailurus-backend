import tarfile
from typing import List
from sqlalchemy import ScalarResult, delete, insert, select
from sqlalchemy.sql.schema import Sequence
from and_platform.cache import clear_public_challenge
from and_platform.api.helper import convert_model_to_dict
from and_platform.core.challenge import (
    ChallengeData,
    check_chall_config,
    get_challenges_directory,
    load_challenge,
    write_chall_info,
    get_challenges_dir_fromid,
)
from and_platform.core.config import get_config
from and_platform.models import ChallengeReleases, Challenges, Servers, db
from flask import Blueprint, jsonify, request
from shutil import rmtree

challenges_blueprint = Blueprint("challenges", __name__, url_prefix="/challenges")


class ChallengeRequest(ChallengeData):
    visibility: List[int]


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
            # Prevent unaltered sequence 
            db.session.execute(Sequence('challenges_id_seq'))
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
        
        set_chall_visibility(chall.id, chall_data.get("visibility", []))

    db.session.commit()
    clear_public_challenge()

    populated_challs = Challenges.query.all()
    return (
        jsonify(status="success", data=convert_model_to_dict(populated_challs)),
        200,
    )


@challenges_blueprint.get("/")
def get_all_challs():
    challenges = db.session.execute(select(Challenges).order_by(Challenges.id)).scalars().all()
    response = []
    for challenge in challenges:
        data = {
            "id" : challenge.id,
            "name" : challenge.name
        }
        response.append(data)

    return jsonify(status="success", data=response), 200

@challenges_blueprint.post("/")
def create_new_chall():
    server_mode = get_config("SERVER_MODE")
    data: ChallengeRequest = request.get_json()

    name = data.get("name")
    description = data.get("description")
    num_expose = data.get("num_expose")
    server_id = data.get("server_id")
    visibility = data.get("visibility")

    if not (name and description and num_expose and visibility) or (
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


    db.session.add(chall)
    db.session.commit()

    set_chall_visibility(chall.id, visibility)

    write_chall_info(
        {
            "name": chall.name,
            "description": chall.description,
            "num_expose": chall.num_expose,
            "server_id": server_id,
            "visibility": visibility,
        },
        chall.id,
    )
    clear_public_challenge()
    
    result: dict = convert_model_to_dict(chall)  # type: ignore
    result["visibility"] = visibility
    result["config_status"] = check_chall_config(chall.id)
    return jsonify(status="success", data=result)


@challenges_blueprint.get("/<int:challenge_id>")
def get_chall(challenge_id: int):
    chall = db.session.get(Challenges, challenge_id)
    if not chall:
        return jsonify(status="not found", message="challenge not found"), 404

    result: dict = convert_model_to_dict(chall)  # type: ignore
    result["visibility"] = list(get_chall_visibility(chall.id))
    result["config_status"] = check_chall_config(chall.id)
    return jsonify(status="success", data=result)


@challenges_blueprint.patch("/<int:challenge_id>")
def update_chall(challenge_id: int):
    server_mode = get_config("SERVER_MODE")
    data: ChallengeRequest = request.get_json()

    chall = db.session.get(Challenges, challenge_id)
    if not chall:
        return jsonify(status="not found", message="challenge not found"), 404

    chall.name = data.get("name", chall.name)
    chall.description = data.get("description", chall.description)
    chall.num_expose = data.get("num_expose", chall.num_expose)
    server_id = data.get("server_id", chall.server_id)
    visibility = data.get("visibility")

    # It might be [], in which we'll completely hide it, this case is to use
    # db's default
    if visibility == None:
        releases = db.session.execute(
            select(ChallengeReleases).filter(
                ChallengeReleases.challenge_id == challenge_id
            )
        ).scalars()
        visibility: List[int] = [r.round for r in releases]  # type: ignore

    if server_mode == "sharing":
        server = db.session.execute(
            select(Servers).filter(Servers.id == server_id)
        ).scalar_one()
        chall.server_id = server.id
        chall.server_host = server.host

    db.session.commit()
    set_chall_visibility(challenge_id, visibility)
    write_chall_info(
        {
            "name": chall.name,
            "description": chall.description,
            "num_expose": chall.num_expose,
            "server_id": server_id,
            "visibility": visibility,
        },
        chall.id,
    )
    
    clear_public_challenge()
    
    result: dict = convert_model_to_dict(chall)  # type: ignore
    result["visibility"] = visibility
    result["config_status"] = check_chall_config(chall.id)
    return jsonify(status="success", data=result)


@challenges_blueprint.delete("/<int:challenge_id>")
def delete_chall(challenge_id: int):
    chall = db.session.get(Challenges, challenge_id)
    if not chall:
        return jsonify(status="not found", message="challenge not found"), 404
    
    set_chall_visibility(challenge_id, [])
    rmtree(get_challenges_dir_fromid(str(challenge_id)))
    clear_public_challenge()
    
    db.session.delete(chall)
    db.session.commit()
    return jsonify(status="success", message=f"challenge {challenge_id} deleted")


@challenges_blueprint.post("/<int:challenge_id>/config")
def upload_config_files(challenge_id: int):
    tar_file = request.files.get("configfile")
    if not tar_file:
        return jsonify(status="failed", message="please submit your file"), 400

    chall = db.session.get(Challenges, challenge_id)
    if not chall:
        return jsonify(status="not found", message="challenge not found"), 404

    challs_dir = get_challenges_directory()
    chall_dir = challs_dir.joinpath(f"chall-{chall.id}")

    tar = tarfile.open(fileobj=tar_file.stream)
    tar.extractall(chall_dir)
    tar.close()

    return jsonify(status="success", message="ok")


def set_chall_visibility(chall_id: int, rounds: List[int]):
    # Delete all releases, then re-insert is the easiest way to handle update
    db.session.execute(
        delete(ChallengeReleases).filter(ChallengeReleases.challenge_id == chall_id)
    )

    if len(rounds) > 0:
        datas = [{"round": round, "challenge_id": chall_id} for round in rounds]
        statement = insert(ChallengeReleases).values(datas)
        db.session.execute(statement)

    db.session.commit()


def get_chall_visibility(chall_id: int) -> ScalarResult[int]:
    return db.session.execute(
        select(ChallengeReleases.round).filter(
            ChallengeReleases.challenge_id == chall_id
        )
    ).scalars()
