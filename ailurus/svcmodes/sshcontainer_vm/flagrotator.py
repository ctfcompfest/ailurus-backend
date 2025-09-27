from ailurus.models import ProvisionMachine, Service

from .utils import execute_remote_command, generate_remote_folder_name
from .types import FlagrotatorTaskType, ServiceDetailType, MachineDetail

import json
import logging

log = logging.getLogger(__name__)

def handler_flagrotator_task(body: FlagrotatorTaskType, **kwargs):
    remote_path = generate_remote_folder_name(body["team_id"], body["challenge_id"])
    flag_value = body["flag_value"]
    
    service: Service = Service.query.filter_by(
        team_id=body["team_id"],
        challenge_id=body["challenge_id"],
    ).first()
    service_detail: ServiceDetailType = json.loads(service.detail)
    
    machine: ProvisionMachine = ProvisionMachine.query.filter_by(
        id=service_detail["machine_id"],
    ).first()
    machine_cred: MachineDetail = json.loads(machine.detail)
    flagrotate_cmd = [
        f"echo '{flag_value}' | sudo tee {remote_path}/flag/flag.txt",
    ]
    
    exec_status = execute_remote_command(
        host=machine.host,
        port=machine.port,
        username=machine_cred["username"],
        private_key=machine_cred["private_key"],
        cmds=flagrotate_cmd,
    )
    if exec_status:
        log.info(f"Successfully rotate flag for team_id={body['team_id']},chall_id={body['challenge_id']}")
