from and_platform.core.security import validteam_only
from and_platform.core.config import get_config
from and_platform.models import db, ChallengeReleases, Flags, Submissions, Solves
from flask import Blueprint, current_app as app, jsonify, request, views
from sqlalchemy import and_

import jwt

submission_blueprint = Blueprint("submission", __name__)
submission_blueprint.before_request(validteam_only)

class Submission(views.MethodView):
    def post(self):
        current_round = get_config("CURRENT_ROUND", 0)
        if current_round == 0:
            return jsonify(status="failed", message="contest has not started yet."), 400

        number_round = get_config("NUMBER_ROUND", 0)
        if current_round > number_round:
            return jsonify(status="failed", message="contest is over."), 400

        current_tick = get_config("CURRENT_TICK")
        
        req_body = request.get_json()
        req_jwt = request.headers.get("authorization").split(" ")[-1]

        # Verifying signature already handled by validteam_only function
        # before calling this function
        current_team = jwt.decode(req_jwt, options={"verify_signature": False})["team"]
        src_challid = int(req_body.get("challenge_id", 0))
        src_flag = req_body.get("flag", "")

        release_challenge = db.session.execute(
            ChallengeReleases.__table__.select().where(
                ChallengeReleases.round == current_round,
                ChallengeReleases.challenge_id == src_challid
            )
        ).fetchone()

        if release_challenge == None:
            return jsonify(status="failed", message="challenge id not found."), 404

        flag_found = db.session.execute(
            Flags.__table__.select().where(
                Flags.challenge_id == src_challid,
                Flags.value == src_flag
            )
        ).fetchone()
        
        submission_verdict = (flag_found != None and flag_found.round == current_round
            and flag_found.tick == current_tick)
        
        new_submission = Submissions(
            team_id = int(current_team["id"]),
            challenge_id = src_challid,
            round = current_round, tick = current_tick,
            value = src_flag, verdict = submission_verdict)

        if not submission_verdict:
            db.session.add(new_submission)
            db.session.commit()
            return jsonify(status="failed", message="flag is wrong or expired."), 400

        # Check for previous correct submission from
        # the same team in the same challenge
        prev_correct_submission = db.session.execute(
            Submissions.__table__.select().where(
                Submissions.team_id == current_team["id"],
                Submissions.flag_id == flag_found.id,
                Submissions.verdict == True
            )    
        ).fetchone()
        
        # Only record new correct submission
        if prev_correct_submission == None:
            new_submission.flag_id = flag_found.id
            db.session.add(new_submission)
            
            if flag_found.team_id == int(current_team["id"]):
                solve = Solves(team_id=int(current_team["id"]), challenge_id=src_challid)
                db.session.add(solve)
        
        db.session.commit()

        return jsonify(status="success", message="flag submitted.")

submission_blueprint.add_url_rule('/submit', view_func=Submission.as_view('submission'))