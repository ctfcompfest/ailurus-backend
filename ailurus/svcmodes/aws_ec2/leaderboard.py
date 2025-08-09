from ailurus.models import db, Team, CheckerResult, CheckerStatus, Flag, ChallengeRelease, Challenge, Submission
from ailurus.utils.config import get_config, is_contest_finished, is_defense_phased
from sqlalchemy import select, func
from typing import List
from .schema import TeamLeaderboardEntry, TeamChallengeLeaderboardEntry

import datetime
import logging

log = logging.getLogger(__name__)

def calculate_team_chall_leaderboard_entry(team_id: int, chall_id: int, freeze_time: datetime.datetime):
    ATTACK_WEIGHT = 1
    DEFENSE_WEIGHT = 3
    
    num_of_session = get_config('CURRENT_ROUND', 0) * get_config('NUMBER_TICK') + get_config('CURRENT_TICK', 0)
    if is_contest_finished():
        num_of_session -= 1

    if freeze_time and datetime.datetime.now(datetime.timezone.utc) > freeze_time:
        num_of_session = get_config('FREEZE_ROUND', 0) * get_config('NUMBER_TICK') + get_config('FREEZE_TICK', 0)
    
    
    result: TeamChallengeLeaderboardEntry = {}
    
    query_distinct_attack_session = select(Submission.tick, Submission.round).join(
            Flag, Flag.id == Submission.flag_id
        ).where(
            Flag.team_id == team_id,
            Submission.team_id != team_id,
            Submission.verdict == True,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
        ).distinct()
    num_broken_tick = db.session.execute(
        select(func.count()).select_from(query_distinct_attack_session.subquery())
    ).scalar()
    num_secure_tick = num_of_session - num_broken_tick
    
    # Number of flag captured including self
    flag_captured = db.session.execute(
        select(func.count(Submission.id)).join(Flag, Flag.id == Submission.flag_id).where(
            Submission.verdict == True,
            Submission.team_id == team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
        )
    ).scalar()
    
    # Number of flag stolen from other teams
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
            CheckerResult.tick > 0,
            CheckerResult.round > 0,
        )
    ).scalar()
    checker_faulty = db.session.execute(
        select(func.count(CheckerResult.id)).where(
            CheckerResult.challenge_id == chall_id,
            CheckerResult.team_id == team_id,
            CheckerResult.status == CheckerStatus.FAULTY,
            CheckerResult.time_created <= freeze_time,
            CheckerResult.tick > 0,
            CheckerResult.round > 0,
        )
    ).scalar()
    

    result["team_id"] = team_id
    result["flag_captured"] = flag_captured
    result["flag_stolen"] = flag_stolen
    result["attack"] = flag_captured * ATTACK_WEIGHT
    result["defense"] = num_secure_tick * DEFENSE_WEIGHT
    result["sla"] = 100
    if (checker_valid + checker_faulty) != 0:
        sla_percentage = checker_valid / (checker_valid + checker_faulty) * 100
        result["sla"] = round(sla_percentage, 2)
    return result

def get_leaderboard(freeze_time: datetime.datetime | None = None, is_admin: bool = False) -> List:
    results: List[TeamLeaderboardEntry] = []

    if is_admin or freeze_time == None:
        # Add 1 hour offset to prevent freeze time
        freeze_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)

    current_round = get_config("CURRENT_ROUND", 0)
    if is_defense_phased():
        current_round = 1
    chall_ids: List[int] = db.session.execute(
        select(ChallengeRelease.challenge_id).where(ChallengeRelease.round <= current_round).distinct(ChallengeRelease.challenge_id)
    ).scalars().all()
    teams: List[Team] = Team.query.all()

    score_by_team = dict()
    for team in teams:
        score_by_team[team.id] = {
            "id": team.id,
            "name": team.name,
            "total_score": 0,
            "challenges": {}
        }
                
    for chall_id in chall_ids:
        score_by_challs = []
        for team in teams:
            chall_score_per_team = calculate_team_chall_leaderboard_entry(team.id, chall_id, freeze_time)
            score_by_challs.append(chall_score_per_team)
        
        for team_score in score_by_challs:
            team_id = team_score["team_id"]
            score_by_team[team_id]["total_score"] += (team_score["attack"] + team_score["defense"]) * team_score["sla"]
            score_by_team[team_id]["challenges"][chall_id] = team_score

    results = score_by_team.values()
    # Calculate total score for each team
    results_sorted = sorted(results, key=(lambda x: x["total_score"]), reverse=True)
    for i in range(len(results_sorted)):
        results_sorted[i]["rank"] = i + 1
    return results_sorted
