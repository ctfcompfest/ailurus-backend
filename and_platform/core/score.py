from and_platform.models import db, ScorePerTicks, Submissions, CheckerQueues, Flags, Challenges, Teams, CheckerVerdict
from and_platform.core.constant import CHECKER_INTERVAL
from typing import List, Optional, TypedDict
from sqlalchemy.sql import func
from datetime import datetime

import time

def calculate_score_tick(round: int, tick: int) -> List[ScorePerTicks]:
    # Prevent duplicate data
    ScorePerTicks.query.filter(ScorePerTicks.round == round, ScorePerTicks.tick == tick).delete()

    data_accum = {}

    correct_submissions = db.session.query(
        Submissions.id,
        Submissions.team_id,
        Submissions.challenge_id,
        Flags.team_id,
    ).join(
        Flags,
        Flags.id == Submissions.flag_id
    ).filter(
        Submissions.round == round,
        Submissions.tick == tick,
        Submissions.verdict == True,
    ).all()

    for row in correct_submissions:
        _, attacker, chall_id, defender = row
        tmp = data_accum.get(chall_id, {})

        atc_tmp = tmp.get(attacker, {"captured": [], "stolen": 0})
        atc_tmp["captured"] = atc_tmp["captured"].append(defender)

        def_tmp = tmp.get(defender, {"captured": [], "stolen": 0})
        def_tmp["stolen"] = def_tmp["stolen"] + 1

        tmp[attacker] = atc_tmp
        tmp[defender] = def_tmp

        data_accum[chall_id] = tmp

    # Waiting time for latest checker
    time.sleep(CHECKER_INTERVAL.seconds)

    checker_results = db.session.query(CheckerQueues).filter(
        CheckerQueues.round == round,
        CheckerQueues.tick == tick,
    ).all()

    for checker_result in checker_results:
        team_id = checker_result.team_id
        chall_id = checker_result.challenge_id
        verdict = checker_result.result
        
        tmp = data_accum.get(chall_id, {})
        team_tmp = tmp.get(team_id, {"faulty": 0, "valid": 0})
        if verdict == CheckerVerdict.VALID:
            team_tmp["valid"] += 1
        elif verdict == CheckerVerdict.FAULTY:
            team_tmp["faulty"] += 1

        tmp[team_id] = team_tmp
        data_accum[chall_id] = tmp

    challs = db.session.query(Challenges.id).all()
    teams = Teams.query.all()
    team_len = len(teams)
    scores = list()

    for chall in challs:
        chall_data = data_accum.get(chall)
        if not chall_data: continue

        for team in teams:
            team_data = chall_data.get(team.id)
            if team_data == None: continue

            flag_captured = team_data.get("captured", [])
            flag_stolen = team_data.get("stolen", 0)
            freq_faulty = team_data.get("faulty", 0)
            freq_valid = team_data.get("valid", 0)
            
            sla_score = 0
            if freq_faulty + freq_valid != 0:
                sla_score = freq_valid / (freq_valid + freq_faulty)
            
            attack_score = 0
            for captured in flag_captured:
                attack_score += team_len * get_service_weight(
                        team_id=captured,
                        challenge_id=chall,
                        current_round=round,
                        current_tick=tick,
                    )
            
            defense_score = (team_len / flag_stolen) * sla_score

            score = ScorePerTicks(
                round = round,
                tick = tick,
                team_id = team.id,
                challenge_id = chall,
                attack_score = attack_score,
                defense_score = defense_score,
                sla = sla_score,
            )
            scores.append(score)
            db.session.add(score)
    db.session.commit()

class TeamChallengeScore(TypedDict):
    challenge_id: int
    flag_captured: int
    flag_stolen: int
    attack: float
    defense: float
    sla: float

class TeamScore(TypedDict):
    team_id: int
    total_score: float
    challenges: List[TeamChallengeScore]    

def get_service_weight(team_id: int, challenge_id: int, current_round: int, current_tick: int) -> float:
    current_stolen = db.session.query(
        Submissions.id,
    ).join(
        Flags,
        Flags.id == Submissions.flag_id
    ).filter(
        Submissions.round == current_round,
        Submissions.tick == current_tick,
        Submissions.verdict == True,
        Flags.team_id == team_id,
        Submissions.team_id != team_id,
        Submissions.challenge_id == challenge_id,
    ).count()
    team_number = db.session.query(Teams.id).count()
    
    return (team_number - current_stolen)/team_number


def get_overall_team_challenge_score(team_id: int, challenge_id: int, before: datetime = None) -> TeamChallengeScore:
    def get_attack_score() -> float:
        return scores[0] if len(scores) == 2 else 0

    def get_defense_score() -> float:
        return scores[1] if len(scores) == 2 else 0

    def get_sla() -> float:    
        filters = [
            CheckerQueues.challenge_id == challenge_id,
            CheckerQueues.team_id == team_id,
            CheckerQueues.result.in_([CheckerVerdict.VALID, CheckerVerdict.FAULTY]),
        ]
        if before:
            filters.append(CheckerQueues.time_created < before)

        all_checker_count = db.session.query(
            CheckerQueues.result,
            func.count(CheckerQueues.id),
        ).filter(*filters).group_by(CheckerQueues.result).all()

        checker_count = {
            0: 0,
            1: 1,
        }
        for elm in all_checker_count:
            status, count = elm
            checker_count[status.value] = count
        if (checker_count[0] + checker_count[1]) > 0:
            sla_rate = checker_count[1] / (checker_count[0] + checker_count[1])
        else:
            sla_rate = 0
        return sla_rate

    flag_captured_filters = [
        Submissions.verdict == True,
        Submissions.team_id == team_id,
        Submissions.challenge_id == challenge_id,
    ]
    flag_stolen_filters = [
        Submissions.verdict == True,
        Flags.team_id == team_id,
        Submissions.team_id != team_id,
        Submissions.challenge_id == challenge_id,
    ]
    if before:
        flag_captured_filters.append(Submissions.time_created < before)
        flag_stolen_filters.append(Submissions.time_created < before)

    all_flag_captured = db.session.query(
        Submissions.id,
        Flags.team_id,
    ).join(
        Flags,
        Flags.id == Submissions.flag_id
    ).filter(*flag_captured_filters).count()

    all_flag_stolen = db.session.query(
        Submissions.id,
        Submissions.team_id,
    ).join(
        Flags,
        Flags.id == Submissions.flag_id
    ).filter(*flag_stolen_filters).count()
    
    score_filters = [
        ScorePerTicks.challenge_id == challenge_id,
        ScorePerTicks.team_id == team_id,
    ]
    if before:
        score_filters.append(ScorePerTicks.time_created < before)

    scores = db.session.query(
        func.sum(ScorePerTicks.attack_score),
        func.sum(ScorePerTicks.defense_score),
    ).filter(*score_filters).group_by(ScorePerTicks.challenge_id, ScorePerTicks.team_id).all()

    return TeamChallengeScore(
        challenge_id=challenge_id,
        flag_captured=all_flag_captured,
        flag_stolen=all_flag_stolen,
        sla=get_sla(),
        attack=get_attack_score(),
        defense=get_defense_score()
    )

def get_overall_team_score(team_id: int, before: datetime = None) -> TeamScore:
    challs = Challenges.query.all()
    team_score = TeamScore(team_id=team_id, total_score=0, challenges=list())
    for chall in challs:
        tmp = get_overall_team_challenge_score(team_id, chall.id, before)
        team_score["total_score"] += tmp["attack"] + tmp["attack"]
        team_score["challenges"].append(tmp)
    return team_score
