from ailurus.models import Team, Challenge, Service
from typing import List, Dict
import flask

def generator_public_services_info(team: Team, challenge: Challenge, services: List[Service]) -> Dict | List | str:
    return "sample"

def handler_svcmanager_request(**kwargs) -> flask.Response:
    is_solved = kwargs['is_solved']
    if is_solved:
        return flask.jsonify(status="success", message="success")
    return flask.jsonify(status="failed", message="failed"), 403
    