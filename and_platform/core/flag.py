from and_platform.models import (
    db,
    Flags,
    Teams,
    Challenges,
    Servers,
)
from and_platform.core.config import get_config
from and_platform.core.service import get_remote_service_path, get_service_path
from and_platform.core.ssh import create_ssh_from_server
from secrets import choice
from string import ascii_lowercase, digits
from typing import List
import os

def generate_flag(current_round: int, current_tick: int) -> List[Flags]:
    CHARSET = ascii_lowercase + digits
    flag_format = get_config("FLAG_FORMAT")
    flag_rndlen = get_config("FLAG_RNDLEN")
    
    flag_format = flag_format.replace("__ROUND__", str(current_round))
    
    teams = db.session.query(Teams.id).all()
    visible_challs = db.session.query(Challenges.id).all()

    flags = list()
    for team in teams:
        for chall in visible_challs:
            SUBRULE = {
                "__TEAM__": str(team.id),
                "__PROBLEM__": str(chall.id),
                "__RANDOM__": "".join([choice(CHARSET) for _ in range(flag_rndlen)]),
            }

            new_flag = flag_format
            for k, v in SUBRULE.items():
                new_flag = new_flag.replace(k, v)
            
            flag = Flags(
                team_id = team.id,
                challenge_id = chall.id,
                round = current_round,
                tick = current_tick,
                value = new_flag,
            )
            flags.append(flag)
            db.session.add(flag)
    db.session.commit()
    return flags

def rotate_flag(current_round: int, current_tick: int):
    sql_query = db.session.query(Flags, Servers)
    if get_config("SERVER_MODE") == "private":
        sql_query = sql_query.join(Teams, Teams.id == Flags.team_id).join(Servers, Servers.id == Teams.server_id)
    elif get_config("SERVER_MODE") == "sharing":
        sql_query = sql_query.join(Challenges, Challenges.id == Flags.challenge_id).join(Servers, Servers.id == Challenges.server_id)
    
    rows = sql_query.filter(Flags.round == current_round, Flags.tick == current_tick).all()
    for row in rows:
        flag = row[0]
        server = row[1]
        
        local_path = os.path.join(get_service_path(flag.team_id, flag.challenge_id), "flag", "flag.txt")
        remote_dir = os.path.join(get_remote_service_path(flag.team_id, flag.challenge_id), "flag", "flag.txt")
        
        with open(local_path, "w") as flagfile_local:
            flagfile_local.write(flag.value)

        with create_ssh_from_server(server) as ssh_conn:
            with ssh_conn.sftp() as sftp_conn:
                with sftp_conn.file(remote_dir, "w") as flagfile_remote:
                    flagfile_remote.write(flag.value.encode())
