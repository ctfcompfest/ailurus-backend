
from typing import TypedDict, Dict

class CheckerTask(TypedDict):
    time_limit: int
    challenge_id: int
    team_id: int
    testcase_checksum: str
    artifact_checksum: str
    current_tick: int
    current_round: int
    time_created: str

class FlagrotatorTask(TypedDict):
    flag_value: str
    flag_order: int # 0: root, 1: user
    challenge_id: int
    team_id: int
    current_tick: int
    current_round: int
    time_created: str

class ServiceManagerTask(TypedDict):
    action: str
    initiator: str
    artifact: str
    challenge_id: int
    team_id: int
    time_created: str

class TeamChallengeLeaderboardEntry(TypedDict):
    flag_captured: int
    flag_stolen: int
    attack: float
    defense: float
    sla: float

class TeamLeaderboardEntry(TypedDict):
    id: int
    name: str
    rank: int
    total_score: float
    challenges: Dict[int, TeamChallengeLeaderboardEntry]