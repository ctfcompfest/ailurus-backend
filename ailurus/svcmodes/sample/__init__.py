from ailurus.models import Team, Challenge, Service, Flag, ProvisionMachine
from typing import List, Dict, Any
import datetime
import json
import flask

def generator_checker_task_body(
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

def generator_flagrotator_task_body(
        service_mode: str,
        flag: Flag,
        services: List[Service],
        provision_machines: List[ProvisionMachine]
    ) -> Dict:
    return {}


def generator_public_services_info(team: Team, challenge: Challenge, services: List[Service]) -> Dict | List | str:
    return "sample"

def handler_svcmanager_request(**kwargs) -> flask.Response:
    is_solved = kwargs['is_solved']
    if is_solved:
        return flask.jsonify(status="success", message="success")
    return flask.jsonify(status="failed", message="failed"), 403
    