from ailurus.utils.config import get_config
from ailurus.utils.svcmode import get_svcmode_module
from pika.adapters.blocking_connection import BlockingChannel

import base64
import json
import logging
import pika
import pika.channel

log = logging.getLogger(__name__)

def create_worker(**kwargs):
    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(kwargs.get("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    rabbitmq_channel.basic_qos(prefetch_count=int(kwargs.get("QUEUE_PREFETCH", "1")))

    log.info("Successfully connect to RabbitMQ.")
    
    queue_checker = kwargs.get("QUEUE_CHECKER_TASK", "checker_task")
    rabbitmq_channel.queue_declare(queue=queue_checker, durable=True)
    rabbitmq_channel.basic_consume(
        queue=queue_checker,
        on_message_callback=(
            lambda ch, method, prop, body: callback_task(queue_checker, ch, method, prop, body, **kwargs)
        )
    )

    queue_flag = kwargs.get("QUEUE_FLAG_TASK", "flag_task")
    rabbitmq_channel.queue_declare(queue=queue_flag, durable=True)
    rabbitmq_channel.basic_consume(
        queue=queue_flag,
        on_message_callback=(
            lambda ch, method, prop, body: callback_task(queue_flag, ch, method, prop, body, **kwargs)
        )
    )

    queue_svcmanager = kwargs.get("QUEUE_SVCMANAGER_TASK", "svcmanager_task")
    rabbitmq_channel.queue_declare(queue=queue_svcmanager, durable=True)
    rabbitmq_channel.basic_consume(
        queue=queue_svcmanager,
        on_message_callback=(
            lambda ch, method, prop, body: callback_task(queue_svcmanager, ch, method, prop, body, **kwargs)
        )
    )

    log.info('Waiting for messages. To exit press CTRL+C')
    rabbitmq_channel.start_consuming()

def callback_task(queue_name: str, ch: BlockingChannel, method, properties, body: bytes, **kwargs):
    with kwargs['flask_app'].app_context():
        body_json = json.loads(base64.b64decode(body))
        log.info(f"Receive new task from {queue_name}.")
        log.debug(f"Task body: {body_json}.")
        svcmodule = get_svcmode_module(get_config("SERVICE_MODE"))
        try:
            if queue_name == kwargs.get("QUEUE_CHECKER_TASK", "checker_task"):
                svcmodule.handler_checker_task(body_json, **kwargs)
            elif queue_name == kwargs.get("QUEUE_FLAG_TASK", "flag_task"):
                svcmodule.handler_flagrotator_task(body_json, **kwargs)
            elif queue_name == kwargs.get("QUEUE_SVCMANAGER_TASK", "svcmanager_task"):
                svcmodule.handler_svcmanager_task(body_json, **kwargs)
        except ValueError as e:
            # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            # ch._message_acknowledged = False
            log.error(f"Error processing task {queue_name}: {str(e)}.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        ch._message_acknowledged = True
    log.info(f"Complete processing task {queue_name}: {method.delivery_tag}.")
