from ailurus.utils.config import get_app_config, get_config, set_config
from ailurus.utils.config import is_contest_started, is_contest_finished, is_contest_paused
from ailurus.worker.flagrotator import rotate_flag
from ailurus.worker.checker import create_checker_task
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta
from flask import Flask
from pika.channel import Channel

import atexit
import pika

def tick_keeper(app: Flask):
    with app.app_context():
        if not is_contest_started() or is_contest_paused() or is_contest_finished():
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

    rotate_flag(current_tick, current_round, app)
    return True


def checker_keeper(app: Flask, queue_channel: Channel):
    with app.app_context():
        if not is_contest_started() or is_contest_paused() or is_contest_finished():
            app.logger.info("[checker-keeper] contest is not running.")
            return False

        current_tick = get_config("CURRENT_TICK")
        current_round = get_config("CURRENT_ROUND")
        app.logger.info(f"[checker-keeper] execute for tick = {current_tick}, round = {current_round}.")

    create_checker_task(current_tick, current_round, app, queue_channel)
    return True

def create_keeper(app):
    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    rabbitmq_channel.queue_declare(get_app_config("QUEUE_CHECKER_TASK"))
    
    scheduler = BackgroundScheduler()
    cron_trigger = CronTrigger(minute="*")
    
    if not scheduler.get_job('tick-keeper'):
        scheduler.add_job(tick_keeper, cron_trigger, args=[app], id='tick-keeper')
    
    if not scheduler.get_job('checker-keeper'):
        scheduler.add_job(checker_keeper, cron_trigger, args=[app, rabbitmq_channel], id='checker-keeper')

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    return scheduler