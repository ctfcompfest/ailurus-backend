from ailurus.models import Challenge, ProvisionMachine

import io
import json
import logging
import paramiko

from .schema import FlagrotatorTaskSchema

log = logging.getLogger(__name__)

def handler_flagrotator_task(body: FlagrotatorTaskSchema, **kwargs):
    first_challenge: Challenge = Challenge.query.order_by(Challenge.id).first()
    provision_machine = ProvisionMachine.query.filter_by(name=f"cloudformation-{first_challenge.id}").first()
    if not provision_machine:
        return log.error("no provision machine found")
    
    provision_machine_detail = json.loads(provision_machine.detail)

    chall_id = body["challenge_id"]
    team_id = body["team_id"]
    chall: Challenge = Challenge.query.filter_by(id=chall_id).first()
    
    flag_value = body["flag_value"]
    flag_path = "/home/samba-lksn/flags/{}-t{}/flag.txt".format(chall.slug, team_id)
    
    samba_ip = provision_machine_detail["SambaServerPrivateIp"]
    samba_privkey = provision_machine_detail["SambaMachinePrivateKey"]
    
    pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(samba_privkey))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(samba_ip, username="ubuntu", pkey=pkey, timeout=5)
        ssh.exec_command("sudo -u samba-lksn bash -c 'echo \"{flag_value}\" > {flag_path}'".format(flag_value=flag_value, flag_path=flag_path))
        ssh.close()
        log.info(f"Successfully rotate flag for team_id: {team_id}, challenge_id={chall_id}.")
        return True
    except paramiko.AuthenticationException:
        log.error(f"Authentication failed for {samba_ip}")
        return None
    except paramiko.SSHException as e:
        log.error(f"Unable to establish SSH connection to {samba_ip}: {str(e)}")
        return None
    except TimeoutError as e:
        log.error(f"Timeout when establish SSH connection to {samba_ip}: {str(e)}")
        return None
    except Exception as e:
        log.error(f"Some error occured: {str(e)}")
        return None
    