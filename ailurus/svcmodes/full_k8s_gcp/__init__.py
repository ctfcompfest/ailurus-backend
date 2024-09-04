from ailurus.models import Team, Challenge, Service
from ailurus.svcmodes.migrations import upgrade
from typing import List, Dict, Mapping, Any

from .flagrotator import handler_flagrotator_task
from .svcmanager import handler_svcmanager_request, handler_svcmanager_task

from .schema import ServiceDetailSchema

import datetime
import flask
import json

def load(app: flask.Flask):
    upgrade()

def generator_public_services_info(team: Team, challenge: Challenge, services: List[Service]) -> Dict | List | str:
    if len(services) == 0: return []
    service_detail: ServiceDetailSchema = json.loads(services[0].detail)
    return service_detail['public_addresses']

def generator_public_services_status_detail(result_detail: Mapping[str, Any]) -> Dict | List | str:
    return result_detail["message"]

def handler_checker_task(body: Mapping[str, Any], **kwargs):
    pass

def get_leaderboard(freeze_time: datetime.datetime | None = None, is_admin: bool = False) -> List:
    pass



