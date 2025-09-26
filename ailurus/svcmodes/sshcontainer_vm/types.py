from typing import TypedDict, List, Dict
import datetime

class ServiceManagerTaskType(TypedDict):
    action: str
    artifact_checksum: str
    challenge_id: int
    team_id: int
    created_at: str
    created_by: str


class ServiceDetailType(TypedDict):
    ServiceDetailCred = TypedDict(
        "ServiceDetailCreds", {"Address": str, "Username": str, "Password": str}
    )
    ExposeService = TypedDict(
        "ExposeService", {"Address": str, "Protocol": str}
    )

    credentials: ServiceDetailCred
    public_addresses: List[ExposeService]


class FlagrotatorTaskType(TypedDict):
    flag_value: str
    flag_order: int
    challenge_id: int
    team_id: int
    current_tick: int
    current_round: int
    time_created: str


class CheckerTaskType(TypedDict):
    time_limit: int
    challenge_id: int
    challenge_slug: str
    team_id: int
    testcase_checksum: str
    artifact_checksum: str
    current_tick: int
    current_round: int
    time_created: str


class CheckerResultDetailType(TypedDict):
    status_detail: str
    exception: str
    checker_output: Dict
    time_finished: datetime.datetime

class MachineDetail(TypedDict):
    username: str
    private_key: str