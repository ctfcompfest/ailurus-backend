from ailurus.utils.config import get_config, set_config
from ailurus.utils.config import is_contest_running
from datetime import datetime, timezone, timedelta
from flask import Flask
from typing import List, Any, Callable

def tick_keeper(app: Flask, callback: Callable, callback_args: List[Any]):
    with app.app_context():
        if not is_contest_running():
            app.logger.info("[tick-keeper] contest is not running.")
            return False

        last_tick_change: datetime = get_config("LAST_TICK_CHANGE", datetime(year=1990, month=1, day=1, tzinfo=timezone.utc))
        tick_duration: int = get_config("TICK_DURATION")
        time_now = datetime.now(timezone.utc).replace(microsecond=0)

        if time_now < last_tick_change or \
            time_now - last_tick_change < timedelta(minutes=tick_duration):
            app.logger.info("[tick-keeper] tick time limit has not been achieved.")
            return False

        current_tick: int = get_config("CURRENT_TICK", 0) + 1
        current_round: int = get_config("CURRENT_ROUND", 1)
        number_tick: int = get_config("NUMBER_TICK")
        if current_tick > number_tick:
            current_tick = 1
            current_round += 1

        app.logger.info(f"[tick-keeper] tick = {current_tick}, round = {current_round}, last_change = {time_now.isoformat()}.")
        set_config("CURRENT_TICK", current_tick)
        set_config("CURRENT_ROUND", current_round)
        set_config("LAST_TICK_CHANGE", time_now.isoformat())
    
    return callback(*callback_args)
