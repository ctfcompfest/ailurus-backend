from and_platform.models import db, ScorePerTicks, Submissions, CheckerQueues, Flags, Challenges, Teams, CheckerVerdict
from and_platform.core.constant import CHECKER_INTERVAL
from typing import List
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
                attack_score += team_len * _get_service_weight(captured, chall, data_accum)
            
            defense_score = team_len * flag_stolen * sla_score

            score = ScorePerTicks(
                round = round,
                tick = tick,
                team_id = team.id,
                attack_score = attack_score,
                defense_score = defense_score,
                sla = sla_score,
            )
            scores.append(score)
            db.session.add(score)
    db.session.commit()


def _get_service_weight(def_id: int, chall_id: int, data: dict):
    chall_data = data.get(chall_id)
    if not chall_data: return 0
    team_data = chall_data.get(def_id)
    if not team_data: return 0
    stolen_cnt = team_data.get("stolen", 0)
    if stolen_cnt == 0: return 1
    return 1/stolen_cnt