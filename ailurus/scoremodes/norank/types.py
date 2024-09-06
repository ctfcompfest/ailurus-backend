from typing import TypedDict, Dict

class TeamChallengeLeaderboardEntry(TypedDict):
    flag_captured: int
    flag_stolen: int
    attack: str
    defense: str
    sla: str

class TeamLeaderboardEntry(TypedDict):
    id: int
    name: str
    rank: int
    total_score: float
    challenges: Dict[int, TeamChallengeLeaderboardEntry]
