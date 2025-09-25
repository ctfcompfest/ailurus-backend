from ailurus.models import db
from ailurus.models import Challenge, Service
from ailurus.utils.config import get_config, get_app_config, is_contest_running

from .models import ManageServicePendingList
from .types import ServiceDetailType, ServiceManagerTaskType

from sqlalchemy import false as sql_false
from typing import Mapping, Any

import base64
import datetime
import flask
import json
import os
import pika
import secrets
import time

def handler_svcmanager_request(**kwargs) -> flask.Response:
    ALLOWED_ACTION = ["provision", "delete", "get_credentials", "reset", "restart"]
    ADMIN_ONLY_ACTION = ["provision", "delete"]
    
    is_admin = kwargs.get('is_admin', False)
    if not kwargs.get('is_allow_manage', False) and not is_admin:
        return flask.jsonify(status="failed", message="failed."), 403

    is_admin = kwargs.get('is_admin', False)
    is_allow_manage = kwargs.get('is_allow_manage', False)
    
    if not is_allow_manage and not is_admin:
        return flask.jsonify(status="failed", message="failed"), 403
    
    request = kwargs.get('request')
    cmd = request.args.get("action")
    if cmd not in ALLOWED_ACTION or not (is_admin or is_contest_running()):
        return flask.jsonify(status="failed", message="action not implemented."), 400
    
    if not is_admin and cmd in ADMIN_ONLY_ACTION:
        return flask.jsonify(status="forbidden", message="forbidden."), 400
    
    chall_id = kwargs.get('challenge_id', 0)
    team_id = kwargs.get('team_id', 0)
    if cmd == "get_credentials":
        service = Service.query.filter_by(challenge_id=chall_id, team_id=team_id).first()
        if not service:
            return flask.jsonify(status="failed", message="invalid command."), 400
        service_detail: ServiceDetailType = json.loads(service.detail)
        return flask.jsonify(status="success", data=service_detail["credentials"])    
    
    challenge: Challenge = Challenge.query.filter_by(id=chall_id).first()
    if not challenge:
        return flask.jsonify(status="failed", message="invalid command."), 400

    pending_list = ManageServicePendingList.query.filter_by(
        team_id=team_id,
        challenge_id=chall_id,
        is_done=sql_false(),
    ).first()
    if pending_list:
        return flask.jsonify(status="failed", message="the last request still in progress."), 400

    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    queue_name = get_app_config("QUEUE_SVCMANAGER_TASK", "svcmanager_task")
    rabbitmq_channel.queue_declare(queue_name, durable=True)

    action_initiator = ("team" if not is_admin else "admin")
    taskbody: ServiceManagerTaskType = {
        "action": cmd,
        "artifact_checksum": challenge.artifact_checksum,
        "testcase_checksum": challenge.testcase_checksum,
        "challenge_id": chall_id,
        "challenge_slug": challenge.slug,
        "team_id": team_id,
        "created_by": action_initiator,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
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
    
    pending_list = ManageServicePendingList(team_id=team_id, challenge_id=chall_id, created_by=action_initiator)
    db.session.add(pending_list)
    db.session.commit()

    return flask.jsonify(status="success", message="success.")

def handler_svcmanager_task(body: Mapping[str, Any], **kwargs):
    time.sleep(5)
    destfolder = os.path.join(get_app_config("DATA_DIR"), "unittest")
    os.makedirs(destfolder, exist_ok=True)    
    logfile = os.path.join(destfolder, "svcmanager-" + secrets.token_hex(6))
    with open(logfile, "w+") as f:
        f.write(json.dumps(body))
    return get_config("CURRENT_ROUND")