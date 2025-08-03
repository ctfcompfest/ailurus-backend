from ailurus.models import db, Team, CheckerResult, CheckerStatus, Flag, ChallengeRelease, Challenge, Submission
from ailurus.utils.config import get_config, is_contest_finished
from functools import cmp_to_key
from sqlalchemy import select, func
from typing import List
from .schema import TeamLeaderboardEntry, TeamChallengeLeaderboardEntry

import datetime
import logging

log = logging.getLogger(__name__)

def calculate_team_chall_leaderboard_entry(team_id: int, chall_id: int, freeze_time: datetime.datetime):
    chall: Challenge = Challenge.query.filter_by(id=chall_id).first()
    num_of_session = get_config('CURRENT_ROUND', 0) * get_config('NUMBER_TICK') + get_config('CURRENT_TICK', 0)
    if is_contest_finished():
        num_of_session -= 1

    if freeze_time and datetime.datetime.now(datetime.timezone.utc) > freeze_time:
        num_of_session = get_config('FREEZE_ROUND', 0) * get_config('NUMBER_TICK') + get_config('FREEZE_TICK', 0)
    
    total_flag = num_of_session * Team.query.count() * chall.num_flag
    attack_max_num = num_of_session * (Team.query.count() - 1) * chall.num_flag
    
    result: TeamChallengeLeaderboardEntry = {}
    
    # Number of flag captured including self
    flag_captured = db.session.execute(
        select(func.count(Submission.id)).join(Flag, Flag.id == Submission.flag_id).where(
            Submission.verdict == True,
            Submission.team_id == team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
        )
    ).scalar()
    attack_percentage = 100
    if total_flag > 0:
        attack_percentage = flag_captured / total_flag * 100.00
    
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

    defense_percentage = 100
    if attack_max_num > 0:
        defense_percentage = (attack_max_num - flag_stolen) / attack_max_num * 100.00
    
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
    

    result["team_id"] = team_id
    result["flag_captured"] = flag_captured
    result["flag_stolen"] = flag_stolen
    result["attack"] = round(attack_percentage, 2)
    result["defense"] = round(defense_percentage, 2)
    result["sla"] = 100
    if (checker_valid + checker_faulty) != 0:
        sla_percentage = checker_valid / (checker_valid + checker_faulty) * 100
        result["sla"] = round(sla_percentage, 2)
    return result

def calculate_group_score(criteria: str, chall_scores: List[TeamChallengeLeaderboardEntry]):
    num_team = len(chall_scores)

    GROUP_THRESHOLD = (0.15, 0.25, 0.35)
    MIN_PEOPLE_THRESHOLD = [max(int(num_team * threshold), 1) for threshold in GROUP_THRESHOLD]
    MAX_PEOPLE_THRESHOLD = [max(int(num_team * threshold * 1.5), 1) for threshold in GROUP_THRESHOLD]
    
    last_idx = 0
    group_score = 3
    sorted_scores = sorted(chall_scores, key=lambda x: x[criteria], reverse=True)

    for min_people, max_people in zip(MIN_PEOPLE_THRESHOLD, MAX_PEOPLE_THRESHOLD):
        score_variance = set(map(lambda x: x[criteria], sorted_scores[last_idx:last_idx + min_people]))
        if len(score_variance) == 1:
            threshold_score = sorted_scores[last_idx][criteria]
        elif last_idx + min_people >= num_team:
            # If we reach the end of the list, we take the last score
            threshold_score = sorted_scores[-1][criteria]
        else:
            threshold_score = sorted_scores[last_idx + min_people - 1][criteria]
            rightmost_idx = min(last_idx + max_people, num_team - 1)
            if sorted_scores[rightmost_idx][criteria] == threshold_score:
                # More than 1.5*y has the same score, so we need to increase the group score
                while sorted_scores[rightmost_idx][criteria] == threshold_score:
                    rightmost_idx -= 1
                    
                threshold_score = sorted_scores[rightmost_idx][criteria]

        while last_idx < num_team and sorted_scores[last_idx][criteria] >= threshold_score:
            sorted_scores[last_idx][f"{criteria}_group_score"] = group_score
            last_idx += 1
        group_score -= 1
    while last_idx < num_team:
        sorted_scores[last_idx][f"{criteria}_group_score"] = 0
        last_idx += 1
    return sorted_scores

def get_leaderboard(freeze_time: datetime.datetime | None = None, is_admin: bool = False) -> List:
    results: List[TeamLeaderboardEntry] = []

    if is_admin or freeze_time == None:
        # Add 1 hour offset to prevent freeze time
        freeze_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)

    current_round = get_config("CURRENT_ROUND", 0)
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
        for k in ["attack", "defense", "sla"]:
            score_by_challs = calculate_group_score(k, score_by_challs)
        
        for team_score in score_by_challs:
            team_id = team_score["team_id"]
            score_by_team[team_id]["total_score"] += team_score["attack_group_score"] + team_score["defense_group_score"] + team_score["sla_group_score"]
            score_by_team[team_id]["challenges"][chall_id] = team_score

    results = score_by_team.values()
    # Calculate total score for each team
    results_sorted = sorted(results, key=(lambda x: x["name"]))
    for i in range(len(results_sorted)):
        results_sorted[i]["rank"] = 1
    return results_sorted
