from and_platform.models import Challenges, Teams, Servers, Services
from and_platform.core.challenge import get_challenges_dir_fromid
from and_platform.core.config import get_app_config, get_config
from and_platform.core.ssh import copy_folder, create_ssh_from_server
from multiprocessing import Pool
from shutil import copytree, ignore_patterns, move
from secrets import token_hex

import os
import yaml

def get_service_path(teamid: int, challid: int):
    return os.path.join(get_app_config("DATA_DIR"), "services", f"svc-t{teamid}-c{challid}")

def get_remote_service_path(teamid: int, challid: int):
    return os.path.join(get_config("REMOTE_DIR"), "services", f"svc-t{teamid}-c{challid}")

def do_remote_provision(team: Teams, challenge: Challenges, server: Servers):
    local_path = get_service_path(team.id, challenge.id)
    remote_path = os.path.join(get_config("REMOTE_DIR"), "services")
    
    with create_ssh_from_server(server) as ssh_conn:
        ssh_conn.sudo(f"mkdir -p {remote_path}")
        ssh_conn.sudo(f"chown -R {server.username}:{server.username} {remote_path}")
        copy_folder(ssh_conn, local_path, remote_path)    

def generate_provision_asset(team: Teams, challenge: Challenges, ports: list[int]):
    SVC_TEMPLATE_DIR = os.path.join(get_app_config("TEMPLATE_DIR"), "service")
    SOURCE_CHALL_DIR = get_challenges_dir_fromid(str(challenge.id))
    dest_dir = get_service_path(team.id, challenge.id)

    copytree(SVC_TEMPLATE_DIR, dest_dir, dirs_exist_ok=True)    
    copytree(SOURCE_CHALL_DIR, dest_dir, ignore=ignore_patterns("test", "challenge.yml", "docker-compose.yml"), dirs_exist_ok=True)
    move(os.path.join(dest_dir, "patchrule.yml"), os.path.join(dest_dir, "meta", "patchrule.yml"))
    
    # Generate compose file
    with open(os.path.join(SOURCE_CHALL_DIR, "docker-compose.yml")) as compose_file:
        compose_str = compose_file.read()
        compose_str = compose_str.replace("__FLAG_DIR__", "./flag")
        compose_str = compose_str.replace("__PORT__", str(ports[0]))
        compose_str = compose_str.replace("__TEAM_SECRET__", team.secret)
    
    compose_data = yaml.safe_load(compose_str)
    for svc in compose_data['services']:
        svc_volume = compose_data['services'][svc].get("volumes", [])
        svc_volume.append("./patch:/.adce_patch")
        svc_volume.append("./meta:/.adce_meta:ro")
        compose_data['services'][svc]["volumes"] = svc_volume
    
    with open(os.path.join(dest_dir, "docker-compose.yml"), "w") as compose_file:
        yaml.safe_dump(compose_data, compose_file)

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

def _do_patch(team_id, challenge_id, server):
    patch_fname = os.path.join(get_service_path(team_id, challenge_id), "patch", "service.patch")
    svc_remote_dir = get_remote_service_path(team_id, challenge_id)
    
    with create_ssh_from_server(server) as ssh_conn:
        ssh_conn.put(patch_fname, os.path.join(svc_remote_dir, "patch"))
        with ssh_conn.cd(svc_remote_dir):
            ssh_conn.run("python3 manage.py apply_patch 2>> logs/error >> logs/log", hide=True)

def do_patch(team_id: int, challenge_id: int, server: Servers):
    pool = Pool(processes=1)
    pool.apply_async(_do_patch, args=(team_id, challenge_id, server))
    pool.close()


def _do_restart(team_id, challenge_id, server):
    svc_remote_dir = get_remote_service_path(team_id, challenge_id)
    
    with create_ssh_from_server(server) as ssh_conn:
        with ssh_conn.cd(svc_remote_dir):
            ssh_conn.run("python3 manage.py restart 2>> logs/error >> logs/log", hide=True)

def do_restart(team_id: int, challenge_id: int, server: Servers):
    pool = Pool(processes=1)
    pool.apply_async(_do_restart, args=(team_id, challenge_id, server))
    pool.close()

def _do_reset(team_id, challenge_id, server):
    svc_local_dir = get_service_path(team_id, challenge_id)
    svc_remote_dir = get_remote_service_path(team_id, challenge_id)
    
    with create_ssh_from_server(server) as ssh_conn:
        local_src = os.path.join(svc_local_dir, "src")
        tmp_src = f"/tmp/{token_hex(8)}" 
        dest_src = os.path.join(svc_remote_dir, "src-tmp")

        copy_folder(ssh_conn, local_src, tmp_src)
        ssh_conn.run(f"mv {tmp_src}/src {dest_src} && rm -rf {tmp_src}")

        with ssh_conn.cd(svc_remote_dir):
            ssh_conn.run("python3 manage.py reset 2>> logs/error >> logs/log", hide=True)

def do_reset(team_id: int, challenge_id: int, server: Servers):
    pool = Pool(processes=1)
    pool.apply_async(_do_reset, args=(team_id, challenge_id, server))
    pool.close()