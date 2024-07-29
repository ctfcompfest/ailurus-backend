from ailurus.models import db, Challenge, ChallengeRelease
from ailurus.schema import ChallengeSchema
from ailurus.utils.config import get_app_config
from ailurus.utils.file import compute_md5
from flask import Blueprint, jsonify, request
from marshmallow.exceptions import ValidationError
from typing import List
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from zipfile import is_zipfile

import json
import os

challenge_blueprint = Blueprint("challenges", __name__, url_prefix="/challenges")
challenge_schema = ChallengeSchema()

@challenge_blueprint.get("/")
def get_all_challenges():
    challs: List[Challenge] = Challenge.query.all()
    return jsonify(status="success", data=challenge_schema.dump(challs, many=True))

@challenge_blueprint.get("/<int:challenge_id>/")
def get_detail_challenge(challenge_id):
    chall: Challenge | None = Challenge.query.filter_by(id=challenge_id).first()
    if chall is None:
        return jsonify(status="not found", message=f"challenge not found."), 404
    return jsonify(status="success", data=challenge_schema.dump(chall))

@challenge_blueprint.post("/")
def create_bulk_challenges():
    if "data" not in request.form:
        return jsonify(status="failed", message="missing 'data' field."), 400
    try:
        request_data = json.loads(request.form.get("data"))
        challs: List[Challenge] = challenge_schema.load(request_data, many=True, transient=True)
        db.session.add_all(challs)
        db.session.commit()
    except ValidationError:
        return jsonify(status="failed", message="missing data for required field."), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify(status="failed", message="new data conflict with the existing."), 400
 
    chall_path = os.path.join(get_app_config("DATA_DIR"), "challenges")
    chall_data = json.loads(request.form.get("data"))

    for i in range(len(challs)):
        chall = challs[i]
        visibility_data = chall_data[i].get("visibility")
        artifactzip = request.files.get(f"artifact[{i}]")
        testcasezip = request.files.get(f"testcase[{i}]")
        if artifactzip and is_zipfile(artifactzip):
            artifactzip.seek(0)
            artifactzip_dest = os.path.join(chall_path, f"artifact-{chall.id}.zip")
            artifactzip.save(artifactzip_dest)
            chall.artifact_checksum = compute_md5(artifactzip_dest)

        if testcasezip and is_zipfile(testcasezip):
            testcasezip.seek(0)
            testcasezip_dest = os.path.join(chall_path, f"testcase-{chall.id}.zip")
            testcasezip.save(testcasezip_dest)
            chall.testcase_checksum = compute_md5(testcasezip_dest)

        if visibility_data:
            db.session.execute(
                delete(ChallengeRelease).where(ChallengeRelease.challenge_id == chall.id)
            )
            chall_releases = [ChallengeRelease(round=i, challenge_id=chall.id) for i in visibility_data]
            db.session.add_all(chall_releases)
    db.session.commit()
    return jsonify(status="success", data=challenge_schema.dump(challs, many=True))


@challenge_blueprint.patch("/<int:challenge_id>/")
def patch_detail_challenge(challenge_id):
    chall: Challenge | None = Challenge.query.filter_by(id=challenge_id).first()
    if chall is None:
        return jsonify(status="not found", message=f"challenge not found."), 404

    request_data = request.get_json()
    if "visibility" in request_data:
        new_visibility = request_data['visibility']
        db.session.execute(
            delete(ChallengeRelease).where(ChallengeRelease.challenge_id == challenge_id)
        )
        chall_releases = [ChallengeRelease(round=i, challenge_id=challenge_id) for i in new_visibility]
        db.session.add_all(chall_releases)
    
    challenge_schema.load(request_data.copy(), instance=chall, partial=True, transient=True)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(status="failed", message="your update conflict with current data."), 400

    return jsonify(status="success", data=challenge_schema.dump(chall))

@challenge_blueprint.post("/<int:challenge_id>/testcase/")
def upload_testcase_challenge(challenge_id):
    chall: Challenge | None = Challenge.query.filter_by(id=challenge_id).first()
    if chall is None:
        return jsonify(status="not found", message="challenge not found."), 404

    tczip = request.files.get("testcase")
    if not tczip:
        return jsonify(status="failed", message="missing 'testcase' field."), 400

    if not is_zipfile(tczip):
        return jsonify(status="failed", message="invalid testcase zip file."), 400
    tczip.seek(0)

    tczip_destpath = os.path.join(get_app_config("DATA_DIR"), "challenges", f"testcase-{challenge_id}.zip")
    tczip.save(tczip_destpath)

    chall.testcase_checksum = compute_md5(tczip_destpath)

    db.session.commit()
    return jsonify(status="success", data=challenge_schema.dump(chall))


@challenge_blueprint.post("/<int:challenge_id>/artifact/")
def upload_artifact_challenge(challenge_id):
    chall: Challenge | None = Challenge.query.filter_by(id=challenge_id).first()
    if chall is None:
        return jsonify(status="not found", message="challenge not found."), 404

    artifactzip = request.files.get("artifact")
    if not artifactzip:
        return jsonify(status="failed", message="missing 'artifact' field."), 400

    if not is_zipfile(artifactzip):
        return jsonify(status="failed", message="invalid artifact zip file."), 400
    artifactzip.seek(0)

    artifactzip_destpath = os.path.join(get_app_config("DATA_DIR"), "challenges", f"artifact-{challenge_id}.zip")
    artifactzip.save(artifactzip_destpath)

    chall.artifact_checksum = compute_md5(artifactzip_destpath)

    db.session.commit()
    return jsonify(status="success", data=challenge_schema.dump(chall))


@challenge_blueprint.delete("/<int:challenge_id>/")
def patch_detail_challenge(challenge_id):
    chall: Challenge | None = Challenge.query.filter_by(id=challenge_id).first()
    if chall is None:
        return jsonify(status="not found", message=f"challenge not found."), 404
    
    for fname in ["testcase", "artifact"]:
        destpath = os.path.join(get_app_config("DATA_DIR"), "challenges", f"{fname}-{challenge_id}.zip")
        try:
            os.remove(destpath)
        except:
            pass

    db.session.execute(
        delete(ChallengeRelease).where(ChallengeRelease.challenge_id == challenge_id)
    )
    db.session.execute(
        delete(Challenge).where(Challenge.id == challenge_id)
    )

    return jsonify(status="success", message="successfully delete challenge.", data=challenge_schema.dump(chall))
