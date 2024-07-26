from ailurus.models import db, Team, Challenge, ChallengeRelease, Service
from ailurus.utils.config import get_app_config, get_config
from ailurus.utils.config import is_contest_running
from ailurus.utils.svcmode import get_svcmode_module
from datetime import datetime, timezone
from flask import Flask
from pika.channel import Channel
from sqlalchemy import select, and_
from typing import List

import itertools
import json
import base64

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
            
            task_body = svcmodule.generate_checker_task_body(
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
