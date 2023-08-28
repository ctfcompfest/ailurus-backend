from and_platform.models import (
    Flags,
    Submissions,
    Solves,
    ScorePerTicks,
    CheckerQueues,
)
from and_platform.core.config import set_config, get_config
from and_platform.core.flag import rotate_flag, generate_flag
from and_platform.core.score import calculate_score_tick
import celery

@celery.shared_task
def init_contest():
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

    set_config("CURRENT_TICK", current_tick + 1)
    set_config("CURRENT_ROUND", current_round)

    # Calculate score for previous tick
    calculate_score_tick(prev_round, prev_tick)