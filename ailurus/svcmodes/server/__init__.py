from ailurus.models import Team, Challenge, Service, Flag, ProvisionMachine
from typing import List, Dict
import datetime
import json

def generate_checker_task_body(
        team: Team,
        challenge: Challenge,
        services: List[Service],
        current_tick: int,
        current_round: int,
        current_time: datetime.datetime
    ) -> Dict:
    service_datas = []
    for service, in services:
        service_datas.append({
            "secret": service.secret,
            "detail": json.loads(service.detail),
        })

    return {
        "team_id": team.id,
        "challenge_id": challenge.id,
        "testcase_checksum": challenge.testcase_checksum,
        "services": service_datas,
        "time_created": current_time.isoformat(),
        "round": current_round,
        "tick": current_tick,
    }

def generate_flagrotator_task_body(
        service_mode: str,
        flag: Flag,
        services: List[Service],
        provision_machines: List[ProvisionMachine]
    ) -> Dict:
    return {}