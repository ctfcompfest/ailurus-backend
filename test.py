import pika
import base64
import json
import secrets

rabbitmq_conn = pika.BlockingConnection(
    pika.URLParameters("amqp://rabbitmq:rabbitmq@localhost:5672/%2F")
)
rabbitmq_channel = rabbitmq_conn.channel()

for i in range(10):
    task_body = {"secret": secrets.token_hex(5)}
    print(task_body)
    rabbitmq_channel.basic_publish(
        exchange='',
        routing_key="checker_task",
        body=base64.b64encode(
            json.dumps(task_body).encode()
        )
    )