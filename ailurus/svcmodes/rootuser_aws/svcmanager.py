from ailurus.models import Challenge, Service, Team
from ailurus.utils.config import get_app_config
from typing import List, Dict

from .schema import ServiceManagerTask

import base64
import datetime
import flask
import json
import logging
import os
import pika
import zipfile

log = logging.getLogger(__name__)

def generator_public_services_info(team: Team, challenge: Challenge, services: List[Service]) -> Dict | List | str:
    """
    Service detail format:
    {
        "publish": {
            "IP": "1.2.3.4",
            "Username": "root",
            "Password": "password",
        },
        "admin": {...}
    }
    """
    return json.loads(services[0].detail).get("publish", {}).get("IP", "")

def handler_svcmanager_request(**kwargs) -> flask.Response:
    ALLOWED_ACTION = ["get_credentials", "provision", "reset", "restart"]

    is_admin = kwargs.get('is_admin', False)
    if not kwargs.get('is_allow_manage', False) and not is_admin:
        return flask.jsonify(status="failed", message="failed."), 403
    request: flask.Request = kwargs.get('request')
    chall_id = kwargs.get('challenge_id')
    team_id = kwargs.get('team_id')
    
    cmd = request.args.get("action")
    if cmd not in ALLOWED_ACTION:
        return flask.jsonify(status="failed", message="invalid command."), 400
    
    if cmd == "get_credentials":
        service = Service.query.filter_by(challenge_id=chall_id, team_id=team_id).first()
        if not service:
            return flask.jsonify(status="failed", message="invalid command."), 400
        return flask.jsonify(status="success", message=json.loads(service.detail).get("publish", {}))

    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    queue_name = get_app_config("QUEUE_SVCMANAGER_TASK", "svcmanager_task")
    rabbitmq_channel.queue_declare(queue_name, durable=True)

    artifact_path = os.path.join(get_app_config("DATA_DIR"), "challenges", f"artifact-{chall_id}.zip")
    with open(artifact_path, "rb") as fp:
        artifact_data = base64.b64encode(fp.read())

    taskbody = {
        "action": cmd,
        "initiator": ("team" if not is_admin else "admin"),
        "artifact": artifact_data.decode(),
        "challenge_id": chall_id,
        "team_id": team_id,
        "time_created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    rabbitmq_channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=base64.b64encode(
            json.dumps(
                taskbody
            ).encode()
        )
    )
    rabbitmq_conn.close()
    
    return flask.jsonify(status="success", message="success.")

def handler_svcmanager_task(body: ServiceManagerTask, **kwargs):
    if body["action"] == "provision" and body["initiator"] == "admin":
        return do_provision(body, **kwargs)
    elif body["action"] == "restart":
        return do_restart(body, **kwargs)
    elif body["action"] == "reset":
        return do_reset(body, **kwargs)

def init_artifact(body, **kwargs):
    chall_id = body["challenge_id"]
    artifactroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", "artifacts")
    artifact_folder = os.path.join(artifact_folder, f"artifact-{chall_id}")
    artifact_zipfile = os.path.join(artifactroot_folder, f"artifact-{chall_id}.zip")
    
    os.makedirs(artifactroot_folder, exist_ok=True)
    with open(artifact_zipfile, 'wb') as fp:
        fp.write(base64.b64decode(body["artifact"]))
    with zipfile.ZipFile(artifact_zipfile, "r") as fp:
        fp.extractall(artifact_folder)

def do_provision(body: ServiceManagerTask, **kwargs):
    init_artifact(body, **kwargs)    
    # TODO:

def do_restart(body: ServiceManagerTask, **kwargs):
    init_artifact(body, **kwargs)    
    # TODO:

def do_reset(body: ServiceManagerTask, **kwargs):
    init_artifact(body, **kwargs)    
    # TODO:
