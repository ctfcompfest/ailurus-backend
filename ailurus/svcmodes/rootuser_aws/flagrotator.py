from ailurus.models import Service

import io
import json
import logging
import paramiko

from .schema import FlagrotatorTask

log = logging.getLogger(__name__)

rootflag_path = "/root/flag.txt"
userflag_path = "/home/ubuntu/flag.txt"

def handler_flagrotator_task(body: FlagrotatorTask, **kwargs):
    flag_value = body["flag_value"]
    flag_path = rootflag_path if body["flag_order"] == 0 else userflag_path

    chall_id = body["challenge_id"]
    team_id = body["team_id"]
    service: Service = Service.query.filter_by(challenge_id=chall_id, team_id=team_id).first()
    if not service:
        log.error(f"Cannot rotate flag, no service found for challenge_id: {chall_id} and team_id: {team_id}")
        return    
    
    service_creds = json.loads(service.detail)["checker"]
    host = service_creds["ip"]
    username = service_creds["username"]
    
    privkey = service_creds["private_key"]
    pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(privkey))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, username=username, pkey=pkey, timeout=5)
        ssh.exec_command(f"sudo sh -c 'echo \"{flag_value}\" > {flag_path}' && cat /dev/null > ~/.bash_history && history -c && exit")
        ssh.close()
        log.info(f"Flag for challenge_id: {chall_id} and team_id: {team_id} successfully rotated.")
        return ssh
    except paramiko.AuthenticationException:
        log.error(f"Authentication failed for {host}")
        return None
    except paramiko.SSHException as e:
        log.error(f"Unable to establish SSH connection to {host}: {str(e)}")
        return None
    except Exception as e:
        log.error(f"Some error occured: {str(e)}")
        return None