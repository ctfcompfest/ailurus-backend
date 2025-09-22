
from typing import TypedDict, Dict

class TeamChallengeLeaderboardEntryType(TypedDict):
    flag_captured: int
    flag_stolen: int
    attack: float
    defense: float
    sla: float

class TeamLeaderboardEntryType(TypedDict):
    id: int
    name: str
    rank: int
    total_score: float
    challenges: Dict[int, TeamChallengeLeaderboardEntryType]