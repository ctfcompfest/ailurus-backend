from ailurus.utils.config import get_app_config
from ailurus.models import db, Team, Challenge, ChallengeRelease, Service
from base64 import b64encode
from datetime import datetime, timezone
from flask import Flask
from pika.channel import Channel
from sqlalchemy import select, and_
from typing import List, Tuple

import json

def create_checker_task(current_tick: int, current_round: int, app: Flask, queue_channel: Channel):
    time_now = datetime.now(timezone.utc).replace(microsecond=0)
    with app.app_context():
        teams: List[Tuple[int]] = db.session.execute(select(Team.id)).all()
        release_challs: List[Tuple[int, str, str]] = db.session.execute(
            select(
                ChallengeRelease.challenge_id,
                Challenge.slug,
                Challenge.testcase_checksum
            ).join(
                ChallengeRelease,
                ChallengeRelease.challenge_id == Challenge.id
            ).where(ChallengeRelease.round == current_round)
        ).all()

        for chall_id, chall_slug, testcase_chksum in release_challs:
            for team_id, in teams:
                services: List[Tuple[Service]] = db.session.execute(
                    select(Service).where(
                        and_(
                            Service.challenge_id == chall_id,
                            Service.team_id == team_id
                        )
                    )
                ).all()
                
                services_data = []
                for service, in services:
                    services_data.append({
                        "secret": service.secret,
                        "detail": json.loads(service.detail),
                    })

                checker_req_body = json.dumps({
                        "team_id": team_id,
                        "challenge_id": chall_id,
                        "challenge_slug": chall_slug,
                        "testcase_checksum": testcase_chksum,
                        "services": services_data,
                        "time_created": time_now.isoformat(),
                        "round": current_round,
                        "tick": current_tick,
                    })
                queue_channel.basic_publish(
                    exchange='',
                    routing_key=get_app_config('QUEUE_CHECKER_TASK'),
                    body=b64encode(checker_req_body.encode())
                )
        app.logger.info("[checker] successfully create check task.")

def execute_checker_task():
    pass

def create_checker_daemon():
    pass