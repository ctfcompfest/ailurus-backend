from ailurus.models import Team, Challenge, Service

from .types import ServiceDetailType

from typing import List, Dict, Mapping, Any

import json


def generator_public_services_info(team: Team, challenge: Challenge, services: List[Service]) -> Dict | List | str:
    if len(services) == 0: return []
    service_detail: ServiceDetailType = json.loads(services[0].detail)
    return service_detail['public_addresses']

def generator_public_services_status_detail(result_detail: Mapping[str, Any]) -> Dict | List | str:
    return result_detail["status_detail"]

