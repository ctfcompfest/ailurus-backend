from datetime import datetime, timedelta
from typing import Callable

import celery
from celery import Celery
from celery.schedules import BaseSchedule, schedule

from and_platform.core.config import get_config, set_config
from and_platform.core.constant import CHECKER_INTERVAL
from and_platform.core.flag import generate_flag, rotate_flag
from and_platform.core.score import calculate_score_tick
from and_platform.models import (
    Challenges,
    CheckerQueues,
    Flags,
    ScorePerTicks,
    Solves,
    Submissions,
)


@celery.shared_task
def init_contest(app=None):
    current_tick = get_config("CURRENT_TICK", 0)
    current_round = get_config("CURRENT_ROUND", 0)
    if current_tick > 0 and current_round > 0:
        return

    if not app:
        app = celery.current_app
    current_round = 1
    current_tick = 1
    set_config("CURRENT_ROUND", current_round)
    set_config("CURRENT_TICK", current_tick)

    Flags.query.delete()
    Submissions.query.delete()
    Solves.query.delete()
    ScorePerTicks.query.delete()
    CheckerQueues.query.delete()

    generate_flag(current_round, current_tick)
    rotate_flag(current_round, current_tick)


@celery.shared_task
def move_tick():
    if is_outside_contest_time():
        return

    prev_tick = get_config("CURRENT_TICK", 0)
    prev_round = get_config("CURRENT_ROUND", 0)
    number_tick = get_config("NUMBER_TICK", 0)

    # Update tick and round counter
    current_tick = prev_tick + 1
    current_round = prev_round
    if current_tick > number_tick:
        current_tick = 1
        current_round = current_round + 1

    generate_flag(current_round, current_tick)
    rotate_flag(current_round, current_tick)

    set_config("CURRENT_TICK", current_tick)
    set_config("CURRENT_ROUND", current_round)

    # Calculate score for previous tick
    calculate_score_tick(prev_round, prev_tick)


def is_outside_contest_time():
    current_tick = get_config("CURRENT_TICK", 0)
    current_round = get_config("CURRENT_ROUND", 0)

    limit_tick = get_config("NUMBER_TICK")
    limit_round = get_config("NUMBER_ROUND")
    return (
        current_round <= 0
        and current_tick <= 0
        and current_round >= limit_round
        and current_tick >= limit_tick
    )


def install_contest_entries(app: Celery):
    time_start = get_config("START_TIME")
    tick_duration = get_config("TICK_DURATION")

    entries = app.conf.beat_schedule
    entries["contest.move-tick"] = {
        "task": "and_platform.core.contest.move_tick",
        "schedule": schedule(run_every=timedelta(seconds=tick_duration)),
        "relative": True,
        "options": {
            "queue": "contest",
            "eta": time_start + timedelta(seconds=tick_duration),
        },
    }

    challenges = Challenges.query.all()
    for chall in challenges:
        schedule_name = f"checker.challenge-{chall.id}"
        entries[schedule_name] = {
            "name": schedule_name,
            "task": "and_platform.checker.tasks.run_checker_for_challenge",
            "args": (chall.id,),
            "schedule": schedule(run_every=CHECKER_INTERVAL, relative=True),
            "relative": True,
            "options": {
                "queue": "checker",
                "eta": time_start + CHECKER_INTERVAL,
            },
        }

    app.conf.beat_schedule = entries
