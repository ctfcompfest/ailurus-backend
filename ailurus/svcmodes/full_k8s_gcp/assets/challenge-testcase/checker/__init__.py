from typing import List, TypedDict, Dict, Tuple, Any
import datetime

class ServiceType(TypedDict):
    id: int
    team_id: int
    challenge_id: int
    order: int
    secret: str
    detail: Dict[str, Any]
    time_created: datetime.datetime

class FlagType(TypedDict):
    id: int
    team_id: int
    challenge_id: int
    round: int
    tick: int
    value: str
    order: int

class CheckerAgentReportType(TypedDict):
    id: int
    team_id: int
    challenge_id: int
    source_ip: str
    time_created: datetime.datetime
    report: Dict[Any, Any]

def main(services: List[ServiceType], flags: List[FlagType], checker_agent_report: CheckerAgentReportType | None) -> Tuple[bool, Dict]:
    service_addresses: List[str] = services[0]["detail"]['public_addresses']

    return True, {
        "status_detail": "valid",
        "time_finished": datetime.datetime.now().isoformat(),
    }