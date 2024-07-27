import pika.channel
from ailurus.utils.svcmode import get_svcmode_module
from pika.adapters.blocking_connection import BlockingChannel
import base64
import json
import pika

def create_worker(**kwargs):
    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(kwargs.get("RABBITMQ_URI"))
    )

    queue_datas = [
        (kwargs.get("QUEUE_CHECKER_TASK", "checker_task"), handle_checker_task),
        (kwargs.get("QUEUE_FLAG_TASK", "flag_task"), handle_flagrotator_task),
        (kwargs.get("QUEUE_SVCMANAGER_TASK", "svcmanager_task"), handle_svcmanager_task),
    ]

    rabbitmq_channel = rabbitmq_conn.channel()
    for queue_data in queue_datas:
        queue_name, queue_callback = queue_data
        rabbitmq_channel.queue_declare(queue=queue_name, durable=True)
        rabbitmq_channel.basic_consume(
            queue=queue_name,
            on_message_callback=(
                lambda ch, method, prop, body: queue_callback(ch, method, prop, body, **kwargs)
            )
        )

    print('Waiting for messages. To exit press CTRL+C')
    rabbitmq_channel.start_consuming()


def handle_checker_task(ch: BlockingChannel, method, properties, body: bytes, **kwargs):
    body_json = json.loads(base64.b64decode(body))
    svcmodule = get_svcmode_module(kwargs.get("SERVICE_MODE"))
    svcmodule.handler_checker_task(body_json, **kwargs)


def handle_flagrotator_task(ch, method, properties, body, **kwargs):
    body_json = json.loads(base64.b64decode(body))
    svcmodule = get_svcmode_module(kwargs.get("SERVICE_MODE"))
    svcmodule.handler_flagrotator_task(body_json, **kwargs)


def handle_svcmanager_task(ch, method, properties, body, **kwargs):
    body_json = json.loads(base64.b64decode(body))
    svcmodule = get_svcmode_module(kwargs.get("SERVICE_MODE"))
    svcmodule.handler_svcmanager_task(body_json, **kwargs)