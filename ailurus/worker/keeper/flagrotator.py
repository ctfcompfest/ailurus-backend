from ailurus.models import db, Flag, Service, ProvisionMachine, Challenge, Team, ChallengeRelease
from ailurus.utils.config import is_contest_running, get_config, get_app_config
from ailurus.utils.contest import generate_flag
from ailurus.utils.svcmode import get_svcmode_module
from flask import Flask
from pika.channel import Channel
from sqlalchemy import select, and_
from typing import Dict, List
from datetime import datetime, timezone, timedelta
import base64
import itertools
import json

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

        flags = []
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