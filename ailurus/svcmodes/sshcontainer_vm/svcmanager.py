from ailurus.models import db
from ailurus.models import Challenge, Service, ProvisionMachine, Team
from ailurus.utils.config import get_config, get_app_config, is_contest_running

from .models import ManageServicePendingList
from .types import ServiceDetailType, ServiceManagerTaskType, MachineDetail
from .utils import init_challenge_asset, execute_remote_command

from sqlalchemy import false as sql_false
from typing import Mapping, Any

import base64
import datetime
import flask
import json
import logging
import os
import pika
import secrets
import time

log = logging.getLogger(__name__)


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
        "challenge_id": chall_id,
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

def handler_svcmanager_task(body: ServiceManagerTaskType, **kwargs):
    log.info("execute %s task for team_id=%s chall_id=%s", body["action"], body["team_id"], body["challenge_id"])

    if body["action"] == "provision" and body["initiator"] == "admin":
        kwargs['artifact_folder'] = init_challenge_asset(body["challenge_id"], body["challenge_slug"], body["artifact_checksum"], "artifact")
        do_provision(body, **kwargs)
    
    if body["action"] == "delete" and body["initiator"] == "admin":
        do_delete(body, **kwargs)
    
    if body["action"] == "reset":
        kwargs['artifact_folder'] = init_challenge_asset(body["challenge_id"], body["challenge_slug"], body["artifact_checksum"], "artifact")
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
        pending_list.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
    
    log.info("finish executing %s task for team_id=%s chall_id=%s", body["action"], body["team_id"], body["challenge_id"])

def generate_folder_name(team_id: int, challenge_id: int):
    return f"/opt/ailurus-container/t{team_id}-c{challenge_id}"

def get_provision_machine(team_id: int, challenge_id: int):
    machine_match_algo = get_config("SSHVM:MACHINE_MATCH_NAME", "challenge_slug")
    if machine_match_algo == "challenge_slug":
        challenge: Challenge = Challenge.query.filter_by(
            id=challenge_id
        ).first()
        if not challenge:
            raise ValueError("Challenge not found")
        return ProvisionMachine.query.filter_by(
            name=challenge.slug
        ).first()

    if machine_match_algo == "team_name":
        team: Team = Team.query.filter_by(
            id=team_id
        ).first()
        if not team:
            raise ValueError("Team not found")
        return ProvisionMachine.query.filter_by(
            name=team.name
        ).first()

    if machine_match_algo == "random":
        raise NotImplementedError("Machine match algo error")

def do_provision(body: ServiceManagerTaskType, **kwargs):
    pass

def do_delete(body: ServiceManagerTaskType, **kwargs):
    team_id = body["team_id"]
    chall_id = body["challenge_id"]
    folder_name = generate_folder_name(team_id, chall_id)
    service: Service = Service.query.filter_by(
        team_id=team_id,
        challenge_id=chall_id,
    ).first()
    if not service:
        raise ValueError(f"Service for team_id={team_id}, chall_id={chall_id} not found")
    service_detail: ServiceDetailType = json.loads(service.detail)
    machine_id = service_detail["machine_id"]
    
    machine: ProvisionMachine = ProvisionMachine.query.filter_by(
        id=machine_id
    ).first()
    if not service:
        raise ValueError(f"Provision machine for service_id={service.id} with machine_id={machine_id} not found")
    
    machine_cred: MachineDetail = json.loads(machine.detail)
    delete_cmds = [
        f"cd {folder_name} && docker compose down --volumes",
        f"rm -rf {folder_name}",
    ]    
    exec_status = execute_remote_command(
        host=machine.host,
        port=machine.port,
        username=machine_cred["username"],
        private_key=machine_cred["private_key"],
        cmds=delete_cmds,
    )
    if not exec_status:
        log.info(f"Failed to delete service for team_id={team_id}, chall_id={chall_id}")
        return
    
    db.session.delete(service)
    db.session.commit()
    log.info(f"Successfully delete service for team_id={team_id}, chall_id={chall_id}")
    
    
def do_reset(body: ServiceManagerTaskType, **kwargs):
    pass


def do_restart(body: ServiceManagerTaskType, **kwargs):
    team_id = body["team_id"]
    chall_id = body["challenge_id"]
    folder_name = generate_folder_name(team_id, chall_id)
    service: Service = Service.query.filter_by(
        team_id=team_id,
        challenge_id=chall_id,
    ).first()
    if not service:
        raise ValueError(f"Service for team_id={team_id}, chall_id={chall_id} not found")
    service_detail: ServiceDetailType = json.loads(service.detail)
    machine_id = service_detail["machine_id"]
    
    machine: ProvisionMachine = ProvisionMachine.query.filter_by(
        id=machine_id
    ).first()
    if not service:
        raise ValueError(f"Provision machine for service_id={service.id} with machine_id={machine_id} not found")
    
    machine_cred: MachineDetail = json.loads(machine.detail)
    restart_cmds = [
        f"cd {folder_name} && docker compose restart",
    ]    
    exec_status = execute_remote_command(
        host=machine.host,
        port=machine.port,
        username=machine_cred["username"],
        private_key=machine_cred["private_key"],
        cmds=restart_cmds,
    )
    if exec_status:
        log.info(f"Successfully restart service for team_id={team_id}, chall_id={chall_id}")