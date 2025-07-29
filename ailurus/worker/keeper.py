from ailurus.models import (
    db,
    Team,
    Challenge,
    ChallengeRelease,
    Flag,
)
from ailurus.utils.config import get_app_config, get_config, set_config
from ailurus.utils.config import is_contest_running
from ailurus.utils.contest import generate_flag

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from datetime import datetime, timezone, timedelta
from flask import Flask
from sqlalchemy import select
from typing import List, Any, Callable

import atexit
import base64
import itertools
import json
import pika
import logging

log = logging.getLogger(__name__)

def create_keeper(app):
    if not get_app_config("KEEPER_ENABLE", False):
        return

    scheduler = BackgroundScheduler()
    cron_trigger = CronTrigger(minute="*")
    
    if not scheduler.get_job('tick-keeper'):
        scheduler.add_job(tick_keeper, cron_trigger, args=[app, flag_keeper, [app]], id='tick-keeper')
    
    if not scheduler.get_job('checker-keeper'):
        scheduler.add_job(checker_keeper, cron_trigger, args=[app], id='checker-keeper')

    log.info("Starting keeper background scheduler.")

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    return scheduler



def tick_keeper(app: Flask, callback: Callable, callback_args: List[Any]):
    with app.app_context():
        if not is_contest_running():
            log.info("tick-keeper: contest is not running.")
            return False

        last_tick_change: datetime = get_config("LAST_TICK_CHANGE", datetime(year=1990, month=1, day=1, tzinfo=timezone.utc))
        tick_duration: int = get_config("TICK_DURATION")
        time_now = datetime.now(timezone.utc).replace(microsecond=0)

        if datetime.now(timezone.utc) >= get_config("FREEZE_TIME"):
            set_config("FREEZE_TICK", get_config("CURRENT_TICK", 0))
            set_config("FREEZE_ROUND", get_config("CURRENT_ROUND", 1))
        
        if time_now < last_tick_change or \
            time_now - last_tick_change < timedelta(minutes=tick_duration):
            log.debug("tick-keeper: tick time limit has not been achieved.")
            return False

        current_tick: int = get_config("CURRENT_TICK", 0) + 1
        current_round: int = get_config("CURRENT_ROUND", 1)
        number_tick: int = get_config("NUMBER_TICK")
        if current_tick > number_tick:
            current_tick = 1
            current_round += 1

        log.info(f"tick-keeper: tick = {current_tick}, round = {current_round}, last_change = {time_now.isoformat()}.")
        
        set_config("CURRENT_TICK", current_tick)
        set_config("CURRENT_ROUND", current_round)
        set_config("LAST_TICK_CHANGE", time_now.isoformat())
    
    return callback(*callback_args)


def checker_keeper(app: Flask):
    with app.app_context():
        if not is_contest_running():
            log.info("checker-keeper: contest is not running.")
            return False

        current_tick = get_config("CURRENT_TICK")
        current_round = get_config("CURRENT_ROUND")
        log.debug(f"checker-keeper: execute for tick = {current_tick}, round = {current_round}.")
        
        time_now = datetime.now(timezone.utc).replace(microsecond=0)
    
        rabbitmq_conn = pika.BlockingConnection(
            pika.URLParameters(get_app_config("RABBITMQ_URI"))
        )
        rabbitmq_channel = rabbitmq_conn.channel()
        rabbitmq_channel.queue_declare(get_app_config("QUEUE_CHECKER_TASK", "checker_task"), durable=True)
        
        log.info("Successfully connect to RabbitMQ.")

        teams: List[Team] = Team.query.all()
        release_challs: List[Challenge] = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(ChallengeRelease.round == current_round)
        ).scalars().all()
        
        for chall, team in itertools.product(release_challs, teams):
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
        log.info(f"checker-keeper: successfully queueing {len(release_challs) * len(teams)} checker tasks.")
                
    return True


def flag_keeper(app: Flask):
    with app.app_context():
        if not is_contest_running():
            log.info("flag-keeper: contest is not running.")
            return False
        
        last_tick_change: datetime = get_config("LAST_TICK_CHANGE", datetime(year=1990, month=1, day=1, tzinfo=timezone.utc))
        time_now = datetime.now(timezone.utc).replace(microsecond=0)
        if time_now - last_tick_change > timedelta(seconds=20):
            log.info("flag-keeper: invalid execution because last tick change is too old.")
            return False

        rabbitmq_conn = pika.BlockingConnection(
            pika.URLParameters(get_app_config("RABBITMQ_URI"))
        )
        rabbitmq_channel = rabbitmq_conn.channel()
        rabbitmq_channel.queue_declare(get_app_config("QUEUE_FLAG_TASK", "flag_task"), durable=True)
        
        log.info("Successfully connect to RabbitMQ.")

        current_tick: int = get_config("CURRENT_TICK")
        current_round: int = get_config("CURRENT_ROUND")
        
        teams: List[Team] = Team.query.all()
        release_challs: List[Challenge] = db.session.execute(
            select(
                Challenge
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(ChallengeRelease.round == current_round)
        ).scalars().all()

        flags: List[Flag] = []
        taskbodys = []
        for team, chall in itertools.product(teams, release_challs):
            for flag_order in range(chall.num_flag):
                flag = generate_flag(current_round, current_tick, team, chall, flag_order)
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
        db.session.add_all(flags)
        db.session.commit()
        
        log.info(f"flag-keeper: successfully generate {len(flags)} flags.")
        
        for taskbody in taskbodys:
            rabbitmq_channel.basic_publish(
                exchange='',
                routing_key=get_app_config('QUEUE_FLAG_TASK', "flag_task"),
                body=base64.b64encode(
                    json.dumps(taskbody).encode()
                )
            )
        rabbitmq_channel.close()
        log.info(f"flag-keeper: successfully broadcast {len(flags)} flag task.")
    return True