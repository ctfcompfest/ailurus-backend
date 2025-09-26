from ailurus.models import db, Team, CheckerResult, CheckerStatus, Flag, ChallengeRelease, Submission, Challenge
from ailurus.utils.config import get_config, is_defense_phased
from functools import cmp_to_key
from sqlalchemy import select, func
from typing import List, Tuple

from .types import TeamLeaderboardEntryType, TeamChallengeLeaderboardEntryType

import datetime

__all__ = ["get_leaderboard", "calculate_submission_score"]

def calculate_team_chall_leaderboard_entry(team_id: int, chall_id: int, freeze_time: datetime.datetime):
    result: TeamChallengeLeaderboardEntryType = {}
    flag_captured = db.session.execute(
        select(func.count(Submission.id)).join(Flag, Flag.id == Submission.flag_id).where(
            Submission.verdict == True,
            Submission.team_id == team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
            Flag.team_id != team_id,
        )
    ).scalar()
    flag_stolen = db.session.execute(
        select(func.count(Submission.id)).join(Flag, Flag.id == Submission.flag_id).where(
            Submission.verdict == True,
            Submission.team_id != team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
            Flag.team_id == team_id,
        )
    ).scalar()
    checker_valid = db.session.execute(
        select(func.count(CheckerResult.id)).where(
            CheckerResult.challenge_id == chall_id,
            CheckerResult.team_id == team_id,
            CheckerResult.status == CheckerStatus.VALID,
            CheckerResult.time_created <= freeze_time,
        )
    ).scalar()
    checker_faulty = db.session.execute(
        select(func.count(CheckerResult.id)).where(
            CheckerResult.challenge_id == chall_id,
            CheckerResult.team_id == team_id,
            CheckerResult.status == CheckerStatus.FAULTY,
            CheckerResult.time_created <= freeze_time,
        )
    ).scalar()
    
    result["flag_captured"] = flag_captured
    result["flag_stolen"] = flag_stolen
    result["attack"] = flag_captured
    result["defense"] = (-0.5 * flag_stolen)
    result["sla"] = 1
    if (checker_valid + checker_faulty) != 0:
        result["sla"] = checker_valid / (checker_valid + checker_faulty)
    return result

def get_leaderboard(freeze_time: datetime.datetime | None = None, is_admin: bool = False) -> List:
    results: List[TeamLeaderboardEntryType] = []

    if is_admin or freeze_time == None:
        freeze_time = datetime.datetime.now(datetime.timezone.utc)

    current_round = get_config("CURRENT_ROUND", 0)
    chall_ids: List[int] = db.session.execute(
        select(ChallengeRelease.challenge_id).where(ChallengeRelease.round <= current_round).distinct(ChallengeRelease.challenge_id)
    ).scalars().all()
    teams: List[Team] = Team.query.all()

    for team in teams:
        team_leaderboard_entry: TeamLeaderboardEntryType = {
            "id": team.id,
            "name": team.name,
            "challenges": {},
            "total_score": 0,
        }
        for chall_id in chall_ids:
            chall_entry = calculate_team_chall_leaderboard_entry(team.id, chall_id, freeze_time)
            team_leaderboard_entry["challenges"][chall_id] = chall_entry
        results.append(team_leaderboard_entry)

    # Calculate total score for each team
    for team in results:
        for chall_id in chall_ids:
            chall_score = team["challenges"][chall_id]
            team["total_score"] += chall_score["attack"] + chall_score["defense"] + chall_score["sla"] * 100
            chall_score["sla"] = "{:.02f}%".format(chall_score["sla"] * 100)

    results_sorted = sorted(results, key=cmp_to_key(lambda x, y: y["total_score"] - x["total_score"]))
    for i in range(len(results_sorted)):
        results_sorted[i]["rank"] = i + 1
    
    
    challs: List[Tuple[Challenge]] = db.session.execute(
        select(Challenge).where(
            Challenge.id.in_(chall_ids)
        ).order_by(Challenge.id)
    ).all()
    challs_data = [
        {"id": chall.id, "title": chall.title}
        for chall, in challs
    ]

    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    challenges = Challenge.get_all_released_challenges(current_round)
    challs_data = [
        {"id": chall.id, "title": chall.title}
        for chall in challenges
    ]
    
    return results_sorted, challs_data

def calculate_submission_score(attacker: Team, defender: Team, challenge: Challenge, flag: Flag):
    return 1.0