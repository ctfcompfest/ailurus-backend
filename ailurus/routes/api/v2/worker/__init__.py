from ailurus.models import db, Challenge, CheckerResult, Team
from ailurus.schema import CheckerResultSchema
from ailurus.utils.config import get_app_config
from ailurus.utils.security import worker_only
from flask import Blueprint, jsonify, request, send_file
from marshmallow.exceptions import ValidationError

import os

worker_blueprint = Blueprint("worker", __name__, url_prefix="/worker")
worker_blueprint.before_request(worker_only)

@worker_blueprint.get("/testcase/<int:challenge_id>")
def get_testcase_challenge(challenge_id):
    chall: Challenge | None = Challenge.query.filter_by(id=challenge_id).first()
    if not chall:
        return jsonify(status="not found", message="challenge not found."), 404
    if chall.testcase_checksum == None:
        return jsonify(status="failed", message="testcase not found."), 400
    tczip_path = os.path.join(get_app_config("DATA_DIR"), "challenges", f"testcase-{chall.id}.zip")
    return send_file(
        tczip_path,
        as_attachment=True,
        download_name=f"testcase-{chall.id}.zip"
    )

@worker_blueprint.get("/artifact/<int:challenge_id>")
def get_artifact_challenge(challenge_id):
    chall: Challenge | None = Challenge.query.filter_by(id=challenge_id).first()
    if not chall:
        return jsonify(status="not found", message="challenge not found."), 404
    if chall.artifact_checksum == None:
        return jsonify(status="failed", message="artifact not found."), 400
    artifactzip_path = os.path.join(get_app_config("DATA_DIR"), "challenges", f"artifact-{chall.id}.zip")
    return send_file(
        artifactzip_path,
        as_attachment=True,
        download_name=f"artifact-{chall.id}.zip"
    )

@worker_blueprint.post("/checkresults")
def submit_checker_result():
    checker_schema = CheckerResultSchema()
    request_data = request.get_json()

    try:
        checkerresult: CheckerResult = checker_schema.load(request_data, transient=True)
        if Team.query.filter_by(id=checkerresult.team_id).count() == 0:
            return jsonify(status="failed", message="team not found."), 400
        if Challenge.query.filter_by(id=checkerresult.challenge_id).count() == 0:
            return jsonify(status="failed", message="challenge not found."), 400
        db.session.add(checkerresult)
        db.session.commit()
    except ValidationError:
        return jsonify(status="failed", message="missing required value."), 400
        
    return jsonify(status="success", data=checker_schema.dump(checkerresult))