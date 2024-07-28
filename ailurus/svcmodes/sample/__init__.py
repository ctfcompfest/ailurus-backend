from ailurus.models import Team, Challenge, Service,CheckerResult
from ailurus.utils.config import get_config, get_app_config
from typing import List, Dict, Mapping, Any

import flask
import json
import os
import secrets

def generator_public_services_info(team: Team, challenge: Challenge, services: List[Service]) -> Dict | List | str:
    return [json.loads(service.detail) for service in services]

def generator_public_services_status_detail(checker_result: CheckerResult) -> Dict | List | str:
    return json.loads(checker_result.detail)

def handler_svcmanager_request(**kwargs) -> flask.Response:
    is_solved = kwargs['is_solved']
    if is_solved:
        return flask.jsonify(status="success", message="success")
    return flask.jsonify(status="failed", message="failed"), 403

def handler_checker_task(body: Mapping[str, Any], **kwargs):
    destfolder = os.path.join(get_app_config("DATA_DIR"), "unittest")
    os.makedirs(destfolder, exist_ok=True)    
    logfile = os.path.join(destfolder, "channel-" + secrets.token_hex(6))
    with open(logfile) as f:
        f.write(json.dumps(body))
    return get_config("CURRENT_ROUND")

def handler_flagrotator_task(body: Mapping[str, Any], **kwargs):
    destfolder = os.path.join(get_app_config("DATA_DIR"), "unittest")
    os.makedirs(destfolder, exist_ok=True)    
    logfile = os.path.join(destfolder, "flag-" + secrets.token_hex(6))
    with open(logfile) as f:
        f.write(json.dumps(body))
    return get_config("CURRENT_ROUND")

def handle_svcmanager_task(body: Mapping[str, Any], **kwargs):
    destfolder = os.path.join(get_app_config("DATA_DIR"), "unittest")
    os.makedirs(destfolder, exist_ok=True)    
    logfile = os.path.join(destfolder, "svcmanager-" + secrets.token_hex(6))
    with open(logfile) as f:
        f.write(json.dumps(body))
    return get_config("CURRENT_ROUND")