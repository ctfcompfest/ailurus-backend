import os
from ailurus.models import Challenge, Service, ProvisionMachine, Team
from ailurus.utils.config import get_app_config, get_config

from ..types import ServiceDetailType, MachineDetail
from ..utils import (
    init_challenge_asset,
    execute_remote_command,
    copy_file_to_remote, 
    generate_remote_folder_name,
)

from typing import List

import json
import logging
import shutil
import secrets
import tarfile

log = logging.getLogger(__name__)


def generate_team_artifact_path(team_id: int, chall_id: int, artifact_checksum: str):
    assetroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", "artifacts")
    asset_folder = os.path.join(assetroot_folder, f"t{team_id}-c{chall_id}-{artifact_checksum}")
    return asset_folder

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

    raise NotImplementedError("Machine match algo error")


def generate_port_base_number(team_id: int, challenge_id: int):
    machine_match_algo = get_config("SSHVM:MACHINE_MATCH_NAME", "challenge_slug")
    
    if machine_match_algo == "challenge_slug":
        challenge: Challenge = Challenge.query.filter_by(
            id=challenge_id
        ).first()
        if not challenge:
            raise ValueError("Challenge not found")
        
        num_team_below = Team.query.filter(
            Team.id < team_id
        ).count()
        base_number = num_team_below * (challenge.num_service + 1) + 40000
        return base_number
    
    if machine_match_algo == "team_name":
        team: Team = Team.query.filter_by(
            id=team_id
        ).first()
        if not team:
            raise ValueError("Team not found")
        challenges_below: List[Challenge] = Challenge.query.filter(
            Challenge.id < challenge_id
        ).all()
        num_chall_services = 0
        for chall in challenges_below:
            num_chall_services += chall.num_service + 1
        base_number = num_chall_services + 40000
        return base_number
    raise NotImplementedError("Machine match algo error")


def get_deployed_machine(team_id: int, challenge_id: int):
    service: Service = Service.query.filter_by(
        team_id=team_id,
        challenge_id=challenge_id,
    ).first()
    if not service:
        raise ValueError(f"Service for team_id={team_id}, chall_id={challenge_id} not found")
    service_detail: ServiceDetailType = json.loads(service.detail)
    machine_id = service_detail["machine_id"]
    
    machine: ProvisionMachine = ProvisionMachine.query.filter_by(
        id=machine_id
    ).first()
    if not machine:
        raise ValueError(f"Provision machine for service_id={service.id} with machine_id={machine_id} not found")
    return machine


def prepare_container(team_id: int, challenge_id: int, artifact_checksum: str):
    artifact_path = init_challenge_asset(challenge_id, artifact_checksum)
    
    challenge: Challenge = Challenge.query.filter_by(id = challenge_id).first()
    
    port_base_number = generate_port_base_number(team_id, challenge_id)
    machine: ProvisionMachine = get_provision_machine(team_id, challenge_id)
    templating_var = {
        "SSH_PORT": port_base_number,
        "EXPOSE_PORT": [port_base_number + i + 1 for i in range(challenge.num_service)],
        "SECRET": secrets.token_hex(3),
        "SSH_PASSWORD": secrets.token_hex(6),
    }
    
    # copy artifact path to team artifact
    team_artifact_path = generate_team_artifact_path(team_id, challenge_id, artifact_checksum)
    shutil.copytree(artifact_path, team_artifact_path)
    
    # Resolve templating
    with open(os.path.join(team_artifact_path, "docker-compose.yml")) as f:
        compose_content = f.read()
    
    mapping = {
        "SECRET": templating_var["SECRET"],
        "SSH_PASSWORD": templating_var["SSH_PASSWORD"],
        "SSH_PORT": templating_var["SSH_PORT"],
    }
    for idx, port in enumerate(templating_var["EXPOSE_PORT"]):
        mapping[f"EXPOSE_PORT_{idx}"] = port
    compose_content = compose_content.format(**mapping)

    with open(os.path.join(team_artifact_path, "docker-compose.yml"), "w") as f:
        f.write(compose_content)
    
    # Archive team artifact
    with tarfile.open(team_artifact_path + ".tar", "w:gz") as tar:
        tar.add(team_artifact_path, arcname=os.path.basename(team_artifact_path))
    shutil.rmtree(team_artifact_path)
    
    # Create service object based on templating value
    service_detail: ServiceDetailType = {
        "machine_id": machine.id,
        "public_addresses": [
            f"{machine.host}:{port}"
            for port in templating_var["EXPOSE_PORT"]
        ],
        "credentials": {
            "Password": templating_var["SSH_PASSWORD"],
            "Address": f"{machine.host}:{templating_var['SSH_PORT']}",
            "Username": "root",
        },
    }
    service = Service(
        team_id=team_id,
        challenge_id=challenge_id,
        secret=templating_var["SECRET"],
        order=0,
        detail=json.dumps(service_detail),
    )
    return service
    

def run_container(team_id: int, challenge_id: int, artifact_checksum: str):
    folder_name = generate_remote_folder_name(team_id, challenge_id)
    machine = get_deployed_machine(team_id, challenge_id)
    machine_cred: MachineDetail = json.loads(machine.detail)
    zip_team_artifacts = f"{generate_team_artifact_path(team_id, challenge_id, artifact_checksum)}.tar"
    exec_status = copy_file_to_remote(
        host=machine.host,
        port=machine.port,
        username=machine_cred["username"],
        private_key=machine_cred["private_key"],
        source_path=zip_team_artifacts,
        dest_path=f"{folder_name}.tar",
    )
    if not exec_status:
        log.info(f"Failed to copy artifact for team_id={team_id}, chall_id={challenge_id}")
        return

    run_cmds = [
        f"mkdir -p {os.path.dirname(folder_name)}",
        f"tar -xz -C {os.path.dirname(folder_name)} -f {folder_name}.tar && rm -f {folder_name}.tar",
        f"cd {folder_name} && docker compose up --build -d",
    ]    
    exec_status = execute_remote_command(
        host=machine.host,
        port=machine.port,
        username=machine_cred["username"],
        private_key=machine_cred["private_key"],
        cmds=run_cmds,
    )
    if not exec_status:
        log.info(f"Failed to run service for team_id={team_id}, chall_id={challenge_id}")
        return False
    log.info(f"Successfully run service for team_id={team_id}, chall_id={challenge_id}")
    return True


def delete_container(team_id: int, challenge_id: int):
    folder_name = generate_remote_folder_name(team_id, challenge_id)
    machine = get_deployed_machine(team_id, challenge_id)
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
        log.info(f"Failed to delete service for team_id={team_id}, chall_id={challenge_id}")
        return False
    log.info(f"Successfully delete service for team_id={team_id}, chall_id={challenge_id}")
    return True


def restart_container(team_id: int, challenge_id: int):
    folder_name = generate_remote_folder_name(team_id, challenge_id)
    machine = get_deployed_machine(team_id, challenge_id)
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
    if not exec_status:
        log.info(f"Failed to restart service for team_id={team_id}, chall_id={challenge_id}")
        return False
    log.info(f"Successfully restart service for team_id={team_id}, chall_id={challenge_id}")
    return True