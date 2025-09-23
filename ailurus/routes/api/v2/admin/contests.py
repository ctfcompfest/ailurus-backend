import base64
import itertools

import pika
from sqlalchemy import select, update
from ailurus.models import ChallengeRelease, db, Submission, Flag, Solve, CheckerResult, ScorePerTick, Config, Team, Challenge
from ailurus.utils.contest import generate_flagrotator_task
from ailurus.utils.config import get_app_config, get_config
from flask import Blueprint, jsonify, request
from typing import List

from datetime import datetime, timezone

import json

contest_blueprint = Blueprint("contests", __name__, url_prefix="/contests")

@contest_blueprint.post('/reset-game/')
def reset_game_contest_data():
    """ Reset the game contest data.
    """
    if not request.json or not request.json.get("confirm", False):
        return jsonify(status="failed", message="Reset game data action should be confirmed."), 400
        
    db.session.query(ScorePerTick).delete()
    db.session.query(CheckerResult).delete()
    db.session.query(Solve).delete()
    db.session.query(Submission).delete()
    db.session.query(Config).where(Config.key.in_([
        "CURRENT_TICK", "CURRENT_ROUND", "FREEZE_TICK", "FREEZE_ROUND", "LAST_PAUSED", "LAST_TICK_CHANGE"
    ])).delete()
    db.session.execute(update(Config).values(value="false").where(Config.key == "IS_CONTEST_PAUSED"))
    db.session.execute(update(Config).values(value="2037-01-01T00:00:00Z").where(Config.key == "START_TIME"))
    db.session.query(Flag).delete()
    db.session.commit()
    return jsonify(status="success", message="Game contest data has been reset."), 200


@contest_blueprint.post('/rotate-flag/')
def rotate_flag_current_tick_round_endpoint():
    """ Force rotate flag for current tick and round
    """
    if not request.json or not request.json.get("confirm", False):
        return jsonify(status="failed", message="Action force rotate flag should be confirmed."), 400
    
    current_tick = get_config("CURRENT_TICK", 0)
    current_round = get_config("CURRENT_TICK", 0)
    if current_tick <= 0 or current_round <= 0:
        return jsonify(status="failed", message="Game has not started yet."), 400
    
    teams: List[Team] = Team.query.all()
    release_challs: List[Challenge] = db.session.execute(
        select(
            Challenge
        ).join(
            ChallengeRelease,
            ChallengeRelease.challenge_id == Challenge.id
        ).where(ChallengeRelease.round == current_round)
    ).scalars().all()
    
    generate_flagrotator_task(teams, release_challs, current_round, current_tick)
    
    return jsonify(status="success", message="Task to force rotate flag has been created."), 200


@contest_blueprint.post('/dry-run/')
def dry_run_contest():
    """ Dry run the contest to check if the checker and worker is valid.
    """
    current_tick = -1
    current_round = -1
    time_now = datetime.now(timezone.utc).replace(microsecond=0)

    request_data = request.get_json()
    team_list = request_data.get("teams", [])
    challenge_list = request_data.get("challenges", [])
    
    teams = db.session.query(Team).filter(Team.id.in_(team_list)).all()
    challenges = db.session.query(Challenge).filter(Challenge.id.in_(challenge_list)).all()

    # Generate dry run flags and flagrotator tasks
    generate_flagrotator_task(teams, challenges, current_round, current_tick)
    
    # Create dry run checker tasks
    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    rabbitmq_channel.queue_declare(get_app_config("QUEUE_CHECKER_TASK", "checker_task"), durable=True)
    
    for chall, team in itertools.product(challenges, teams):
        task_body = {
            "challenge_id": chall.id,
            "team_id": team.id,
            "testcase_checksum": chall.testcase_checksum,
            "artifact_checksum": chall.artifact_checksum,
            "current_tick": current_tick,
            "current_round": current_round,
            "time_created": time_now.isoformat(),
        }
        
        rabbitmq_channel.basic_publish(
            exchange='',
            routing_key=get_app_config('QUEUE_CHECKER_TASK', "checker_task"),
            body=base64.b64encode(
                json.dumps(task_body).encode()
            )
        )
    rabbitmq_channel.close()
        
    rabbitmq_conn.close()
    return jsonify(status="success", message="Successfully trigger dry run"), 200
    