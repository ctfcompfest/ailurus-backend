import base64
import itertools

import pika
from ailurus.models import db, Submission, Flag, Solve, CheckerResult, ScorePerTick, Config, Team, Challenge
from ailurus.utils.contest import generate_or_get_flag
from ailurus.utils.config import get_app_config
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
    db.session.query(Config).where(Config.key.in_(["CURRENT_TICK", "CURRENT_ROUND", "FREEZE_TICK", "FREEZE_ROUND"])).delete()
    db.session.query(Flag).delete()
    db.session.commit()
    return jsonify(status="success", message="Game contest data has been reset."), 200

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
    flags: List[Flag] = []
    taskbodys = []
    for team, chall in itertools.product(teams, challenges):
        for flag_order in range(chall.num_flag):
            flag = generate_or_get_flag(current_tick, current_round, team, chall, flag_order)
            taskbody = {
                "flag_value": flag.value,
                "flag_order": flag.order,
                "challenge_id": chall.id,
                "team_id": team.id,                    
                "current_tick": current_tick,
                "current_round": current_round,
                "time_created": time_now.isoformat(),
            }
            
            flags.append(flag)
            taskbodys.append(taskbody)
        db.session.commit()
    
    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    rabbitmq_channel.queue_declare(get_app_config("QUEUE_FLAG_TASK", "flag_task"), durable=True)
    
    for taskbody in taskbodys:
        rabbitmq_channel.basic_publish(
            exchange='',
            routing_key=get_app_config('QUEUE_FLAG_TASK', "flag_task"),
            body=base64.b64encode(
                json.dumps(taskbody).encode()
            )
        )
    rabbitmq_channel.close()
    
    # Create dry run checker tasks
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
    