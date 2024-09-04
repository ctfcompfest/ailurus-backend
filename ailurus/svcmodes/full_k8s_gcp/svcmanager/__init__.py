from ailurus.models import db, Challenge, Service
from ailurus.utils.config import get_app_config, is_contest_running

from ..schema import ServiceManagerTaskSchema, ServiceDetailSchema
from ..utils import init_challenge_asset
from ..models import ManageServicePendingList

from .build_image import do_build_image
from .delete import do_delete
from .provision import do_provision
from .reset import do_reset
from .restart import do_restart

import base64
import datetime
import flask
import json
import logging
import pika

log = logging.getLogger(__name__)

def handler_svcmanager_request(**kwargs) -> flask.Response:
    ALLOWED_ACTION = ["build_image", "provision", "delete", "get_credentials", "reset", "restart"]
    ADMIN_ONLY_ACTION = ["build_image", "provision", "delete"]

    is_admin = kwargs.get('is_admin', False)
    if not kwargs.get('is_allow_manage', False) and not is_admin:
        return flask.jsonify(status="failed", message="failed."), 403
    
    request: flask.Request = kwargs.get('request')
    chall_id = kwargs.get('challenge_id', 0)
    team_id = kwargs.get('team_id', 0)
    
    cmd = request.args.get("action")
    if cmd not in ALLOWED_ACTION or not (is_admin or is_contest_running()):
        return flask.jsonify(status="failed", message="action not implemented."), 400
    
    if not is_admin and cmd in ADMIN_ONLY_ACTION:
        return flask.jsonify(status="forbidden", message="forbidden."), 400

    if cmd == "get_credentials":
        service = Service.query.filter_by(challenge_id=chall_id, team_id=team_id).first()
        if not service:
            return flask.jsonify(status="failed", message="invalid command."), 400
        service_detail: ServiceDetailSchema = json.loads(service.detail)
        return flask.jsonify(status="success", data=service_detail["credentials"])

    challenge: Challenge = Challenge.query.filter_by(id=chall_id).first()
    if not challenge:
        return flask.jsonify(status="failed", message="invalid command."), 400

    pending_list = ManageServicePendingList.query.filter_by(
        team_id=team_id,
        challenge_id=chall_id,
        is_done=False,
    ).first()
    if pending_list:
        return flask.jsonify(status="success", message="in progress."), 200

    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    queue_name = get_app_config("QUEUE_SVCMANAGER_TASK", "svcmanager_task")
    rabbitmq_channel.queue_declare(queue_name, durable=True)

    taskbody: ServiceManagerTaskSchema = {
        "action": cmd,
        "initiator": ("team" if not is_admin else "admin"),
        "artifact_checksum": challenge.artifact_checksum,
        "testcase_checksum": challenge.testcase_checksum,
        "challenge_id": chall_id,
        "challenge_slug": challenge.slug,
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
    
    pending_list = ManageServicePendingList(team_id=team_id, challenge_id=chall_id)
    db.session.add(pending_list)
    db.session.commit()

    return flask.jsonify(status="success", message="success.")

def handler_svcmanager_task(body: ServiceManagerTaskSchema, **kwargs):
    log.info("execute %s task for team_id=%s chall_id=%s", body["action"], body["team_id"], body["challenge_id"])
    
    if body["action"] == "build_image" and body["initiator"] == "admin":
        kwargs['artifact_folder'] = init_challenge_asset(body["challenge_id"], body["challenge_slug"], body["artifact_checksum"], "artifact")
        kwargs['testcase_folder'] = init_challenge_asset(body["challenge_id"], body["challenge_slug"], body["testcase_checksum"], "testcase")
        do_build_image(body, **kwargs)
    
    if body["action"] == "provision" and body["initiator"] == "admin":
        kwargs['artifact_folder'] = init_challenge_asset(body["challenge_id"], body["challenge_slug"], body["artifact_checksum"], "artifact")
        kwargs['testcase_folder'] = init_challenge_asset(body["challenge_id"], body["challenge_slug"], body["testcase_checksum"], "testcase")
        do_provision(body, **kwargs)
    
    if body["action"] == "delete" and body["initiator"] == "admin":
        do_delete(body, **kwargs)
    
    if body["action"] == "reset":
        do_reset(body, **kwargs)
    
    if body["action"] == "restart":
        do_restart(body, **kwargs)
    
    pending_list = ManageServicePendingList.query.filter_by(
        team_id=body["team_id"],
        challenge_id=body["challenge_id"],
        is_done=False,
    ).first()
    if pending_list:
        pending_list.is_done = True
        db.session.commit()

    log.info("finish executing %s task for team_id=%s chall_id=%s", body["action"], body["team_id"], body["challenge_id"])
    