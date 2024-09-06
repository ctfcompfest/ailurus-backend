from typing import TypedDict, List, Dict
import datetime

class ServiceManagerTaskType(TypedDict):
    action: str
    initiator: str
    artifact_checksum: str
    testcase_checksum: str
    challenge_id: int
    challenge_slug: str
    team_id: int
    time_created: str

class ServiceDetailType(TypedDict):
    ServiceDetailCreds = TypedDict('ServiceDetailCreds', {'Address':str, 'Username':str, 'Private Key':str})

    credentials: ServiceDetailCreds
    public_adresses: List[str]

class FlagrotatorTaskType(TypedDict):
    flag_value: str
    flag_order: int
    challenge_id: int
    team_id: int
    current_tick: int
    current_round: int
    time_created: str

class CheckerResultDetailType(TypedDict):
    status_detail: str
    exception: str
    checker_output: Dict
    time_finished: datetime.datetime
