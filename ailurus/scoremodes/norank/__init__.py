from ailurus.models import db, Team, CheckerResult, CheckerStatus, Flag, ChallengeRelease, Challenge, Submission
from ailurus.utils.config import get_config
from functools import cmp_to_key
from sqlalchemy import select, func
from typing import List, Tuple

from .types import TeamLeaderboardEntry, TeamChallengeLeaderboardEntry

import datetime

__all__ = ["get_leaderboard", "calculate_submission_score"]

def calculate_team_chall_leaderboard_entry(team_id: int, chall_id: int, freeze_time: datetime.datetime):
    chall: Challenge = Challenge.query.filter_by(id=chall_id).first()
    total_flag = get_config('CURRENT_ROUND', 0) * get_config('CURRENT_TICK', 0) * Team.query.count() * chall.num_flag
    
    result: TeamChallengeLeaderboardEntry = {}
    flag_captured = db.session.execute(
        select(func.count(Submission.id)).join(Flag, Flag.id == Submission.flag_id).where(
            Submission.verdict == True,
            Submission.team_id == team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
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
    
    attack_percentage = flag_captured / total_flag * 100.00
    defense_percentage = (total_flag - flag_stolen) / total_flag * 100.00

    result["flag_captured"] = flag_captured
    result["flag_stolen"] = flag_stolen
    result["attack"] = f"{attack_percentage:.2f}%"
    result["defense"] = f"{defense_percentage:.2f}%"
    result["sla"] = "100%"
    if (checker_valid + checker_faulty) != 0:
        sla_percentage = checker_valid / (checker_valid + checker_faulty) * 100
        result["sla"] = f"{sla_percentage:.2f}%"
    return result

def get_leaderboard(freeze_time: datetime.datetime | None = None, is_admin: bool = False) -> Tuple[List, List]:
    results: List[TeamLeaderboardEntry] = []

    if is_admin or freeze_time == None:
        freeze_time = datetime.datetime.now(datetime.timezone.utc)

    current_round = get_config("CURRENT_ROUND", 0)
    chall_ids: List[int] = db.session.execute(
        select(ChallengeRelease.challenge_id).where(ChallengeRelease.round <= current_round).distinct(ChallengeRelease.challenge_id)
    ).scalars().all()
    teams: List[Team] = Team.query.all()

    for team in teams:
        team_leaderboard_entry: TeamLeaderboardEntry = {
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
    results_sorted = sorted(results, key=cmp_to_key(lambda x, y: x["name"] < y["name"]))
    for i in range(len(results_sorted)):
        results_sorted[i]["rank"] = 1\
        
    challs: List[Tuple[Challenge]] = db.session.execute(
        select(Challenge).where(
            Challenge.id.in_(
                ChallengeRelease.get_challenges_from_round(current_round)
            )
        ).order_by(Challenge.id)
    ).all()
    challs_data = {
        chall.id: {"id": chall.id, "title": chall.title}
        for chall, in challs
    }

    return results_sorted, challs_data

def calculate_submission_score(attacker: Team, defender: Team, challenge: Challenge, flag: Flag):
    return 1.0