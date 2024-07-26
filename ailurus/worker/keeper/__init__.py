from ailurus.worker.keeper.tick import tick_keeper
from ailurus.worker.keeper.checker import checker_keeper
from ailurus.worker.keeper.flagrotator import flag_keeper
from ailurus.utils.config import get_app_config
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import atexit
import pika

def create_keeper(app):
    if not app.config.get("KEEPER_ENABLE", False):
        return

    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    rabbitmq_channel.queue_declare(get_app_config("QUEUE_CHECKER_TASK", "checker_task"))
    rabbitmq_channel.queue_declare(get_app_config("QUEUE_FLAG_TASK", "flag_task"))
    
    scheduler = BackgroundScheduler()
    cron_trigger = CronTrigger(minute="*")
    
    if not scheduler.get_job('tick-keeper'):
        scheduler.add_job(tick_keeper, cron_trigger, args=[app, flag_keeper, [app, rabbitmq_channel]], id='tick-keeper')
    
    if not scheduler.get_job('checker-keeper'):
        scheduler.add_job(checker_keeper, cron_trigger, args=[app, rabbitmq_channel], id='checker-keeper')

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    return scheduler
