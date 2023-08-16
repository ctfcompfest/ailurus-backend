from and_platform.models import Challenges, Teams, Servers, Services
from and_platform.core.config import get_app_config

import os
import yaml
import shutil

def _get_service_path(teamid: int, challid: int):
    return f"svc-t{teamid}-c{challid}"

def do_remote_provision(team: Teams, challenge: Challenges, server: Servers, ports: list[int]):
    pass

def do_provision_private_mode(team: Teams, challenges: list[Challenges], server: Servers):
    pass

def do_provision_sharing_mode(challenge: Challenges, teams: list[Teams], server: Servers):
    DATA_DIR = get_app_config("DATA_DIR")
    CHALLS_DIR = os.path.join(DATA_DIR, "challenges")
    SVCS_DIR = os.path.join(DATA_DIR, "services")
    SOURCE_DIR = os.path.join(CHALLS_DIR, challenge.id)
    
    with open(os.path.join(SOURCE_DIR, "docker-compose.yml")) as compose_file:
        compose_data = yaml.safe_load(compose_file)

    for svc in compose_data['services']:
        svc_volume = compose_data['services'][svc].get("volumes", [])
        svc_volume.append("./patch:/.adce_patch")
        compose_data['services'][svc]["volumes"] = svc_volume
    
    for team in teams:    
        dest_dir = os.path.join(SVCS_DIR, _get_service_path(team.id, challenge.id))
        shutil.copytree(SOURCE_DIR, dest_dir, ignore=("test", "challenge.yml", "docker-compose.yml"), dirs_exist_ok=True)
        
        team_port = 5000 + challenge.id * 100 + team.id
        with open(os.path.join(dest_dir, "docker-compose.yml"), "rw") as compose_file:
            yaml.safe_dump(compose_data, compose_file)
            compose_file.seek(0)
            compose_str = compose_file.read(0)
            compose_str = compose_str.replace("__FLAG_DIR__", "./flag")
            compose_str = compose_str.replace("__PORT__", str(team_port))
            compose_str = compose_str.replace("__TEAM_SECRET__", team.secret)
            compose_file.write(compose_str)