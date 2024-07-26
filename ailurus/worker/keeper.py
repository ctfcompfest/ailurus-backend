from ailurus.models import (
    db,
    Team,
    Challenge,
    ChallengeRelease,
    Service,
    ProvisionMachine,
    Flag,
)
from ailurus.utils.config import get_app_config, get_config, set_config
from ailurus.utils.config import is_contest_running
from ailurus.utils.contest import generate_flag
from ailurus.utils.svcmode import get_svcmode_module

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from datetime import datetime, timezone, timedelta
from flask import Flask
from pika.channel import Channel
from sqlalchemy import select, and_
from typing import List, Any, Callable

import atexit
import base64
import itertools
import json
import pika

def create_keeper(app):
    if not app.config.get("KEEPER_ENABLE", False):
        return

    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    rabbitmq_channel.queue_declare(get_app_config("QUEUE_CHECKER_TASK", "checker_task"))
    rabbitmq_channel.queue_declare(get_app_config("QUEUE_FLAG_TASK", "flag_task"))
    
    scheduler = BackgroundScheduler()
    cron_trigger = CronTrigger(minute="*")
    
    if not scheduler.get_job('tick-keeper'):
        scheduler.add_job(tick_keeper, cron_trigger, args=[app, flag_keeper, [app, rabbitmq_channel]], id='tick-keeper')
    
    if not scheduler.get_job('checker-keeper'):
        scheduler.add_job(checker_keeper, cron_trigger, args=[app, rabbitmq_channel], id='checker-keeper')

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    return scheduler



def tick_keeper(app: Flask, callback: Callable, callback_args: List[Any]):
    with app.app_context():
        if not is_contest_running():
            app.logger.info("[tick-keeper] contest is not running.")
            return False

        last_tick_change: datetime = get_config("LAST_TICK_CHANGE", datetime(year=1990, month=1, day=1, tzinfo=timezone.utc))
        tick_duration: int = get_config("TICK_DURATION")
        time_now = datetime.now(timezone.utc).replace(microsecond=0)

        if time_now < last_tick_change or \
            time_now - last_tick_change < timedelta(minutes=tick_duration):
            app.logger.info("[tick-keeper] tick time limit has not been achieved.")
            return False

        current_tick: int = get_config("CURRENT_TICK", 0) + 1
        current_round: int = get_config("CURRENT_ROUND", 1)
        number_tick: int = get_config("NUMBER_TICK")
        if current_tick > number_tick:
            current_tick = 1
            current_round += 1

        app.logger.info(f"[tick-keeper] tick = {current_tick}, round = {current_round}, last_change = {time_now.isoformat()}.")
        set_config("CURRENT_TICK", current_tick)
        set_config("CURRENT_ROUND", current_round)
        set_config("LAST_TICK_CHANGE", time_now.isoformat())
    
    return callback(*callback_args)


def checker_keeper(app: Flask, queue_channel: Channel):
    with app.app_context():
        if not is_contest_running():
            app.logger.info("[checker-keeper] contest is not running.")
            return False

        service_mode = get_config("SERVICE_MODE")
        svcmodule = get_svcmode_module(service_mode=service_mode)
    
        current_tick = get_config("CURRENT_TICK")
        current_round = get_config("CURRENT_ROUND")
        app.logger.info(f"[checker-keeper] execute for tick = {current_tick}, round = {current_round}.")
        
        time_now = datetime.now(timezone.utc).replace(microsecond=0)
    
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
            services: List[Service] = db.session.execute(
                select(Service).where(
                    and_(
                        Service.challenge_id == chall.id,
                        Service.team_id == team.id
                    )
                )
            ).scalars().all()
            
            task_body = svcmodule.generator_checker_task_body(
                team=team,
                challenge=chall,
                services=services,
                current_tick=current_tick,
                current_round=current_round,
                current_time=time_now
            )
            
            queue_channel.basic_publish(
                exchange='',
                routing_key=get_app_config('QUEUE_CHECKER_TASK', "checker_task"),
                body=base64.b64encode(
                    json.dumps(task_body).encode()
                )
            )
                
    return True


def flag_keeper(app: Flask, queue_channel: Channel):
    with app.app_context():
        if not is_contest_running():
            app.logger.info("[flag-keeper] contest is not running.")
            return False
        
        last_tick_change: datetime = get_config("LAST_TICK_CHANGE", datetime(year=1990, month=1, day=1, tzinfo=timezone.utc))
        time_now = datetime.now(timezone.utc).replace(microsecond=0)
        if time_now - last_tick_change > timedelta(seconds=20):
            app.logger.info("[flag-keeper] invalid execution: last tick change is too old.")
            return False

        current_tick: int = get_config("CURRENT_TICK")
        current_round: int = get_config("CURRENT_ROUND")

        service_mode = get_config("SERVICE_MODE")
        provision_machines: List[ProvisionMachine] = ProvisionMachine.query.all()
        svcmodule = get_svcmode_module(service_mode=service_mode)
        
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
            services: List[Service] = db.session.execute(
                select(Service).where(
                    and_(
                        Service.challenge_id == chall.id,
                        Service.team_id == team.id
                    )
                )
            ).scalars().all()
            
            for flag_order in range(chall.num_flag):
                flag = generate_flag(current_round, current_tick, team, chall, flag_order)
                taskbody = svcmodule.generator_flagrotator_task_body(
                    flag=flag,
                    services=services,
                    provision_machines=provision_machines
                )

                flags.append(flag)
                taskbodys.append(taskbody)
        db.session.add_all(flags)
        db.session.commit()
        
        app.logger.info(f"[flag-keeper] successfully generate {len(flags)} flags.")
        
        for taskbody in taskbodys:
            queue_channel.basic_publish(
                exchange='',
                routing_key=get_app_config('QUEUE_FLAG_TASK', "flag_task"),
                body=base64.b64encode(
                    json.dumps(taskbody).encode()
                )
            )
        
        app.logger.info(f"[flag-keeper] successfully broadcast {len(flags)} flag task.")
    return True