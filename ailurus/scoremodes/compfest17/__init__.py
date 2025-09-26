from ailurus.models import db, Team, CheckerResult, CheckerStatus, Flag, ChallengeRelease, Submission, Challenge, Solve
from ailurus.utils.config import get_config
from functools import cmp_to_key
from sqlalchemy import select, func
from typing import List, Tuple

from .types import TeamLeaderboardEntryType, TeamChallengeLeaderboardEntryType

import datetime

__all__ = ["get_leaderboard", "calculate_submission_score"]

def calculate_attack_score(total_submissions: int) -> float:
    if total_submissions <= 0:
        return 0.0
    
    ranges = [
        (141, 10.0),
        (82, 5.0),
        (112, 3.33),
        (112, 2.5),
        (112, 2.0),
        (112, 1.66),
        (112, 1.42),
        (112, 1.25),
        (113, 1.11),
    ]
    
    attack_score = 0.0
    remaining = total_submissions
    
    for range_size, points in ranges:
        if remaining <= 0:
            break
        count_in_range = min(remaining, range_size)
        attack_score += count_in_range * points
        remaining -= count_in_range
    
    if remaining > 0:
        attack_score += remaining * 1.0
        
    return attack_score

def calculate_team_chall_leaderboard_entry(team_id: int, chall_id: int, freeze_time: datetime.datetime):
    result: TeamChallengeLeaderboardEntryType = {}
    
    flag_captured = db.session.execute(
        select(func.count(Submission.id))
        .join(Flag, Flag.id == Submission.flag_id)
        .where(
            Submission.verdict == True,
            Submission.team_id == team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
            Flag.team_id != team_id,
        )
    ).scalar() or 0
    
    attack_score = calculate_attack_score(flag_captured)
    
    flag_stolen = db.session.execute(
        select(func.count(Submission.id)).join(Flag, Flag.id == Submission.flag_id).where(
            Submission.verdict == True,
            Submission.team_id != team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
            Flag.team_id == team_id,
        )
    ).scalar()
    
    n_team_solved = db.session.execute(
        select(func.count(Solve.id))
        .where(
            Solve.challenge_id == chall_id,
            Solve.time_created <= freeze_time
        )
    ).scalar() or 0
    
    current_tick = get_config("CURRENT_TICK", 0)
    defense_score = 0.0
    DEF = 10.0
    
    stolen_ticks = db.session.execute(
        select(Submission.tick, func.count(Submission.id).label('stolen_count'))
        .join(Flag, Flag.id == Submission.flag_id)
        .where(
            Submission.verdict == True,
            Submission.team_id != team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
            Flag.team_id == team_id,
            Submission.tick <= current_tick
        )
        .group_by(Submission.tick)
    ).all()
    
    stolen_tick_set = {tick for tick, count in stolen_ticks if count > 0}
    
    for tick in range(1, current_tick + 1):
        is_not_stolen = 1 if tick not in stolen_tick_set else 0
        defense_score += DEF * is_not_stolen
    
    defense_score *= n_team_solved
    
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
    
    sla = 1.0
    if (checker_valid + checker_faulty) != 0:
        sla = checker_valid / (checker_valid + checker_faulty)
    
    result["flag_captured"] = flag_captured
    result["flag_stolen"] = flag_stolen
    result["attack"] = attack_score 
    result["defense"] = defense_score
    result["sla"] = sla
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
            attack_score = chall_score["attack"] * chall_score["sla"]
            defense_score = chall_score["defense"] * chall_score["sla"]
            team["total_score"] += attack_score + defense_score
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

    return results_sorted, challs_data
    
def calculate_submission_score(attacker: Team, defender: Team, challenge: Challenge, flag: Flag):
    return 1.0

