from typing import List, TypedDict, Dict, Tuple, Any
import datetime
import requests

class ServiceDetailType(TypedDict):
    ServiceDetailCred = TypedDict(
        "ServiceDetailCreds", {"Address": str, "Username": str, "Password": str}
    )

    credentials: ServiceDetailCred
    public_addresses: List[str]
    machine_id: int


class ServiceType(TypedDict):
    id: int
    team_id: int
    challenge_id: int
    order: int
    secret: str
    detail: ServiceDetailType
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

def create_result(stt):
    verdict = True
    if stt != "valid": verdict = False

    return verdict, {
        "status_detail": stt,
        "time_finished": datetime.datetime.now().isoformat(),
    }

def main(services: List[ServiceType], flags: List[FlagType], checker_agent_report: CheckerAgentReportType | None) -> Tuple[bool, Dict]:
    secret = services[0]["secret"]
    service_addresses: List[str] = services[0]["detail"]['public_addresses']
    if checker_agent_report is None:
        return create_result("agent lost")
    
    agent_time = checker_agent_report["time_created"]
    time_now = datetime.datetime.now(datetime.timezone.utc)
    if not (time_now - agent_time) <= datetime.timedelta(seconds=60):
        return create_result("agent lost")

    if not checker_agent_report["report"]["is_code_valid"]:
        return create_result("service faulty")

    try:
        resp = requests.get("http://{}/?password=P4ssw0rdR4Aah45144&cmd=bombom".format(service_addresses[0]), timeout=1)
        if resp.text.find("bombom") == -1:
            return create_result("service faulty")
    except requests.exceptions.Timeout:
        return create_result("not reachable")
    return create_result("valid")