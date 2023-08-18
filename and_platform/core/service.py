from and_platform.models import db, Challenges, Teams, Servers, Services
from and_platform.core.config import get_app_config, get_config
from and_platform.core.ssh import copy_folder, create_ssh_from_server
from shutil import copytree, ignore_patterns

import os
import yaml

def _get_service_path(teamid: int, challid: int):
    return os.path.join(get_app_config("DATA_DIR"), "services", f"svc-t{teamid}-c{challid}")

def do_remote_provision(team: Teams, challenge: Challenges, server: Servers):
    local_path = _get_service_path(team.id, challenge.id)
    remote_path = os.path.join(get_config("REMOTE_DIR"), "service")
    
    with create_ssh_from_server(server) as ssh_conn:
        ssh_conn.sudo(f"mkdir -p {remote_path}")
        ssh_conn.sudo(f"chown -R {server.username}:{server.username} {remote_path}")
        copy_folder(ssh_conn, local_path, remote_path)    

def generate_provision_asset(team: Teams, challenge: Challenges, ports: list[int]):
    DATA_DIR = get_app_config("DATA_DIR")
    CHALLS_DIR = os.path.join(DATA_DIR, "challenges")
    
    SVC_TEMPLATE_DIR = os.path.join(get_app_config("TEMPLATE_DIR"), "service")
    SOURCE_CHALL_DIR = os.path.join(CHALLS_DIR, str(challenge.id))

    dest_dir = _get_service_path(team.id, challenge.id)
    copytree(SVC_TEMPLATE_DIR, dest_dir, dirs_exist_ok=True)    
    copytree(SOURCE_CHALL_DIR, dest_dir, ignore=ignore_patterns("test", "challenge.yml", "docker-compose.yml"), dirs_exist_ok=True)

    # Generate compose file
    with open(os.path.join(SOURCE_CHALL_DIR, "docker-compose.yml")) as compose_file:
        compose_data = yaml.safe_load(compose_file)
    for svc in compose_data['services']:
        svc_volume = compose_data['services'][svc].get("volumes", [])
        svc_volume.append("./patch:/.adce_patch")
        compose_data['services'][svc]["volumes"] = svc_volume
    
    with open(os.path.join(dest_dir, "docker-compose.yml"), "w+") as compose_file:
        yaml.safe_dump(compose_data, compose_file)
        compose_file.seek(0)
        compose_str = compose_file.read()
        compose_str = compose_str.replace("__FLAG_DIR__", "./flag")
        compose_str = compose_str.replace("__PORT__", str(ports[0]))
        compose_str = compose_str.replace("__TEAM_SECRET__", team.secret)
        compose_file.write(compose_str)

def do_provision(team: Teams, challenge: Challenges, server: Servers):
    ports = [50000 + team.id * 100 + challenge.id]
    generate_provision_asset(team, challenge, ports)
    do_remote_provision(team, challenge, server)

    services = list()
    for i in range(len(ports)):
        tmp_service = Services(
            team_id = team.id,
            challenge_id = challenge.id,
            order = i,
            address = f"{server.host}:{ports[i]}"
        )
        services.append(tmp_service)
    return services