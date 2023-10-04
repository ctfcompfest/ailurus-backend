import math
from and_platform.cache import cache
from and_platform.models import (
    db,
    ScorePerTicks,
    Submissions,
    CheckerQueues,
    Flags,
    Challenges,
    Teams,
    CheckerVerdict,
)
from typing import List, TypedDict
from sqlalchemy.sql import func
from datetime import datetime

TeamID = int
ChallID = int


class TeamData(TypedDict):
    captured: list[TeamID]
    stolen: int
    sla: dict[ChallID, float]


class SLAData(TypedDict):
    faulty: int
    valid: int


@cache.memoize()
def calculate_score_tick(round: int, tick: int):
    # Prevent duplicate data
    ScorePerTicks.query.filter(
        ScorePerTicks.round == round, ScorePerTicks.tick == tick
    ).delete()

    current_leaderboard = get_leaderboard()
    data_accum: dict[ChallID, dict[TeamID, TeamData]] = {}

    correct_submissions = (
        db.session.query(
            Submissions.id,
            Submissions.team_id,
            Submissions.challenge_id,
            Flags.team_id,
        )
        .join(Flags, Flags.id == Submissions.flag_id)
        .filter(
            Submissions.round == round,
            Submissions.tick == tick,
            Submissions.verdict == True,
        )
        .all()
    )

    for row in correct_submissions:
        _, attacker, chall_id, defender = row
        tmp = data_accum.get(chall_id, {})

        atc_tmp = tmp.get(
            attacker,
            {"captured": [], "stolen": 0, "sla": {}},
        )
        atc_tmp["captured"].append(defender)

        def_tmp = tmp.get(
            defender,
            {"captured": [], "stolen": 0, "sla": {}},
        )
        def_tmp["stolen"] = def_tmp["stolen"] + 1

        tmp[attacker] = atc_tmp
        tmp[defender] = def_tmp

        data_accum[chall_id] = tmp

    checker_results = (
        db.session.query(CheckerQueues)
        .filter(
            CheckerQueues.round == round,
            CheckerQueues.tick == tick,
        )
        .all()
    )

    team_slas: dict[TeamID, dict[ChallID, SLAData]] = {}
    for checker_result in checker_results:
        team_id = checker_result.team_id
        chall_id = checker_result.challenge_id
        verdict = checker_result.result

        team_tmp = team_slas.get(team_id, {})
        current_chall_data = team_tmp.get(
            chall_id,
            {"valid": 0, "faulty": 0},
        )
        if verdict == CheckerVerdict.VALID:
            current_chall_data["valid"] += 1
        elif verdict == CheckerVerdict.FAULTY:
            current_chall_data["faulty"] += 1

        team_tmp[chall_id] = current_chall_data
        team_slas[team_id] = team_tmp

    challs = db.session.query(Challenges.id).all()
    teams: list[Teams] = Teams.query.all()
    team_len = len(teams)
    challs_len = len(challs)
    scores = list()

    for chall_row in challs:
        chall = chall_row[0]
        chall_data = data_accum.get(chall)

        for team in teams:
            team_sla = team_slas.get(
                team.id,
                {
                    cid[0]: {
                        "faulty": 0,
                        "valid": 0,
                    }
                    for cid in challs
                },
            )

            attack_score = 0.0
            current_pos = 1
            for i, player in enumerate(current_leaderboard):
                if player["team_id"] == team.id:
                    current_pos = i + 1
                    break

            if chall_data:
                team_data = chall_data.get(team.id, {"captured": []})  # type: ignore
                flag_captured = team_data.get("captured", [])
                for captured in flag_captured:
                    total_stolen = get_total_stolen(
                        team_id=captured,
                        challenge_id=chall,
                        current_round=round,
                        current_tick=tick,
                    )
                    current_score = math.sqrt(1 / total_stolen)
                    captured_pos = 1
                    for i, player in enumerate(current_leaderboard):
                        if player["team_id"] == captured:
                            captured_pos = i + 1
                            break

                    if current_pos > captured_pos:
                        current_score *= 1 + (current_pos - captured_pos) / (
                            team_len - 1
                        )

                    attack_score += current_score

            defense_score = 0.0
            total_stolen = get_total_stolen(
                team_id=team.id,
                challenge_id=chall,
                current_round=round,
                current_tick=tick,
            )

            service_sla = team_sla.get(
                chall,
                {"faulty": 0, "valid": 0},
            )
            sla_score = 0.0
            if service_sla["faulty"] + service_sla["valid"] > 0:
                sla_score = service_sla["valid"] / (
                    service_sla["faulty"] + service_sla["valid"]
                )

            total_not_owning = team_len - 1 - total_stolen
            defense_score += math.sqrt(
                (total_not_owning + challs_len * sla_score)
                / (team_len - 1 + challs_len)
            )

            score = ScorePerTicks(
                round=round,
                tick=tick,
                team_id=team.id,
                challenge_id=chall,
                attack_score=attack_score,
                defense_score=defense_score,
                sla=sla_score,
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


@cache.memoize()
def get_total_stolen(
    team_id: int,
    challenge_id: int,
    current_round: int,
    current_tick: int,
) -> float:
    return (
        db.session.query(
            Submissions.id,
        )
        .join(Flags, Flags.id == Submissions.flag_id)
        .filter(
            Submissions.round == current_round,
            Submissions.tick == current_tick,
            Submissions.verdict == True,
            Flags.team_id == team_id,
            Submissions.team_id != team_id,
            Submissions.challenge_id == challenge_id,
        )
        .count()
    )


@cache.memoize()
def get_overall_team_challenge_score(
    team_id: int, challenge_id: int, before: datetime | None = None
) -> TeamChallengeScore:
    flag_captured_filters = [
        Submissions.verdict == True,
        Submissions.team_id == team_id,
        Flags.team_id != team_id,
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

    all_flag_captured = (
        db.session.query(
            Submissions.id,
            Flags.team_id,
        )
        .join(Flags, Flags.id == Submissions.flag_id)
        .filter(*flag_captured_filters)
        .count()
    )

    all_flag_stolen = (
        db.session.query(
            Submissions.id,
            Submissions.team_id,
        )
        .join(Flags, Flags.id == Submissions.flag_id)
        .filter(*flag_stolen_filters)
        .count()
    )

    score_filters = [
        ScorePerTicks.challenge_id == challenge_id,
        ScorePerTicks.team_id == team_id,
    ]
    if before:
        score_filters.append(ScorePerTicks.time_created < before)

    scores = (
        db.session.query(
            func.avg(ScorePerTicks.sla),
            func.sum(ScorePerTicks.attack_score),
            func.sum(ScorePerTicks.defense_score),
        )
        .filter(*score_filters)
        .group_by(ScorePerTicks.challenge_id, ScorePerTicks.team_id)
        .first()
    )

    return TeamChallengeScore(
        challenge_id=challenge_id,
        flag_captured=all_flag_captured,
        flag_stolen=all_flag_stolen,
        sla=scores[0] if scores and len(scores) == 3 else 0,
        attack=scores[1] if scores and len(scores) == 3 else 0,
        defense=scores[2] if scores and len(scores) == 3 else 0,
    )


@cache.memoize()
def get_overall_team_score(team_id: int, before: datetime | None = None) -> TeamScore:
    challs = Challenges.query.all()
    team_score = TeamScore(team_id=team_id, total_score=0, challenges=list())
    for chall in challs:
        tmp = get_overall_team_challenge_score(team_id, chall.id, before)
        team_score["total_score"] += tmp["attack"] + tmp["defense"] + tmp["sla"]
        team_score["challenges"].append(tmp)
    return team_score


def get_leaderboard():
    teams = Teams.query.all()
    scoreboard: list[TeamScore] = []
    for team in teams:
        team_score = get_overall_team_score(team.id)
        scoreboard.append(team_score)

    scoreboard_sort = sorted(scoreboard, key=lambda x: x["total_score"], reverse=True)
    return scoreboard_sort
