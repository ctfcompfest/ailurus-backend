import base64
import itertools
import logging
from typing import List

import pika
from ailurus.models import (
    db,
    Flag,
    Team,
    Challenge,
)
from ailurus.utils.config import get_app_config, get_config, set_config
from datetime import datetime, timezone
from secrets import choice
from string import ascii_lowercase, digits
import json

log = logging.getLogger(__name__)

def update_paused_status(newvalue: bool | str):
    if isinstance(newvalue, str):
        newvalue = json.loads(newvalue)
    
    if get_config("IS_CONTEST_PAUSED") and not newvalue:
        tick_duration = get_config("TICK_DURATION")
        last_tick_change = get_config("LAST_TICK_CHANGE")
        last_paused = get_config("LAST_PAUSED")
        
        if last_tick_change != None and last_paused != None:
            diff_minutes = last_paused - last_tick_change
            pivot_last_tick_change = datetime.now(timezone.utc).replace(microsecond=0, second=0) - diff_minutes
            set_config("LAST_TICK_CHANGE", pivot_last_tick_change.isoformat())

        set_config("IS_CONTEST_PAUSED", "false")
    elif not get_config("IS_CONTEST_PAUSED") and newvalue:
        time_now = datetime.now(timezone.utc).replace(microsecond=0, second=0)
        set_config("LAST_PAUSED", time_now.isoformat())
        set_config("IS_CONTEST_PAUSED", "true")

def calculate_submission_score(attacker: Team, defender: Team, challenge: Challenge, flag: Flag):
    return 1.0

def generate_flag_value(current_round: int, current_tick: int, team: Team, challenge: Challenge, order: int = 0) -> Flag:
    CHARSET = ascii_lowercase + digits
    flag_format = get_config("FLAG_FORMAT")
    flag_rndlen = get_config("FLAG_RNDLEN", 0)
    
    SUBRULE = {
        "__ROUND__": str(current_round),
        "__TICK__": str(current_tick),
        "__ORDER__": str(order),
        "__TEAM__": str(team.id),
        "__PROBLEM__": str(challenge.id),
        "__RANDOM__": "".join([choice(CHARSET) for _ in range(flag_rndlen)]),
    }
    new_flag = flag_format[:]
    for k, v in SUBRULE.items():
        new_flag = new_flag.replace(k, v)
    return new_flag

def insert_or_overwrite_flag_in_db(flag_value: str, current_round: int, current_tick: int, team_id: int, challenge_id: int, flag_order: int = 0, **kwargs):
    existing_flagdb = db.session.query(Flag).filter_by(
        team_id=team_id,
        challenge_id=challenge_id,
        round=current_round,
        tick=current_tick,
        order=flag_order
    ).first()
    if existing_flagdb:
        existing_flagdb.value = flag_value
        db.session.commit()
        return existing_flagdb
    
    flag = Flag(
        team_id = team_id,
        challenge_id = challenge_id,
        round = current_round,
        tick = current_tick,
        value = flag_value,
        order = flag_order,
    )
    db.session.add(flag)
    db.session.commit()
    db.session.refresh(flag)
    return flag

def generate_flagrotator_task(teams: List[Team], challenges: List[Challenge], current_round: int, current_tick: int):
    taskbodys = []
    time_now = datetime.now(timezone.utc).replace(microsecond=0)
    for team, chall in itertools.product(teams, challenges):
        for flag_order in range(chall.num_flag):
            flag_value = generate_flag_value(current_tick, current_round, team, chall, flag_order)
            taskbody = {
                "flag_value": flag_value,
                "flag_order": flag_order,
                "challenge_id": chall.id,
                "team_id": team.id,                    
                "current_tick": current_tick,
                "current_round": current_round,
                "time_created": time_now.isoformat(),
            }
            
            taskbodys.append(taskbody)
    
    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    rabbitmq_channel.queue_declare(get_app_config("QUEUE_FLAG_TASK", "flag_task"), durable=True)
    log.info("Successfully connect to RabbitMQ.")
    
    for taskbody in taskbodys:
        rabbitmq_channel.basic_publish(
            exchange='',
            routing_key=get_app_config('QUEUE_FLAG_TASK', "flag_task"),
            body=base64.b64encode(
                json.dumps(taskbody).encode()
            )
        )
    
    log.info(f"successfully generate {len(taskbodys)} flags.")
    
    rabbitmq_channel.close()
    rabbitmq_conn.close()
    return taskbodys