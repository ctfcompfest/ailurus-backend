from base64 import b64decode
from io import StringIO
import re
from typing import List
from ailurus.utils.config import get_app_config, get_config

import logging
import os
import requests
import zipfile
import paramiko

log = logging.getLogger(__name__)

def generate_remote_folder_name(team_id: int, challenge_id: int):
    return f"/opt/ailurus-container/t{team_id}-c{challenge_id}"

def init_challenge_asset(chall_id, asset_checksum=None, asset_type="artifact"):
    if asset_checksum == None: return None

    assetroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", f"{asset_type}s")
    asset_folder = os.path.join(assetroot_folder, f"{chall_id}-{asset_checksum}")
    asset_zipfile = os.path.join(assetroot_folder, f"{chall_id}-{asset_checksum}.zip")
    
    os.makedirs(assetroot_folder, exist_ok=True)
    if not os.path.exists(asset_folder):
        log.info(f"{asset_type} file not found, will download the file.")

        link_download = get_app_config("WEBAPP_URL") + "/api/v2/worker/{}/{}/".format(asset_type, chall_id)
        log.debug(f"downloading {asset_type} file from {link_download}.")
        
        worker_secret = get_config("WORKER_SECRET")
        response = requests.get(link_download, headers={"X-WORKER-SECRET": worker_secret})
        log.debug(f"response from webapp: {response.status_code}.")
        
        with open(asset_zipfile, 'wb') as asset_type_zip:
            asset_type_zip.write(response.content)
    
        with zipfile.ZipFile(asset_zipfile, "r") as asset_type_zip_file:
            log.debug(f"extracting {asset_type} zipfile to {asset_folder}.")
            asset_type_zip_file.extractall(asset_folder)
    return asset_folder

def rebuild_private_key(private_key: str):
    sshkey_split = private_key.split("\n")
    sshkey_header = sshkey_split[0]

    if sshkey_header.find("RSA") != -1:
        key_mode = "ssh-rsa"
    elif sshkey_header.find("OPENSSH") != -1:
        sshkey = "".join(sshkey_split[1:-1])
        # Find "ssh-<something>" except "ssh-key"
        key_mode = re.search(b"ssh-(?!key)[A-Za-z0-9]+", b64decode(sshkey.encode())).group(0).decode()
    
    keyfile = StringIO(private_key)
    if key_mode == "ssh-ed25519":
        return paramiko.Ed25519Key.from_private_key(keyfile)
    if key_mode == "ssh-ecdsa":
        return paramiko.ECDSAKey.from_private_key(keyfile)
    if key_mode == "ssh-dss":
        return paramiko.DSSKey.from_private_key(keyfile)
    if key_mode == "ssh-rsa":
        return paramiko.RSAKey.from_private_key(keyfile)
    
    raise ValueError(f"could not recognize {key_mode} as a key type.")

def execute_remote_command(host: str, port: int, username: str, private_key: str, cmds: List[str]):
    private_key_obj = rebuild_private_key(private_key)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=host, port=port, username=username, pkey=private_key_obj, timeout=5)
        for cmd in cmds:
            _, stdout, stderr = ssh.exec_command(cmd)
            log.info(f"cmd: {cmd}")
            log.info(f"stdout: {stdout.read()}")
            log.info(f"stderr: {stderr.read()}")
        ssh.close()
        log.info(f"Remote command successfully executed")
        return True
    except paramiko.AuthenticationException:
        log.error(f"Authentication failed for {host}")
        return None
    except paramiko.SSHException as e:
        log.error(f"Unable to establish SSH connection to {host}: {str(e)}")
        return None
    except TimeoutError as e:
        log.error(f"Timeout when establish SSH connection to {host}: {str(e)}")
        return None
    except Exception as e:
        log.error(f"Some error occured: {str(e)}")
        return None

def copy_file_to_remote(host: str, port: int, username: str, private_key: str, source_path: str, dest_path: str):
    private_key_obj = rebuild_private_key(private_key)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    execute_remote_command(host, port, username, private_key, [f"sudo mkdir -p -m 777 {os.path.dirname(dest_path)}"])
    
    try:
        ssh.connect(hostname=host, port=port, username=username, pkey=private_key_obj, timeout=5)
        ftp_client = ssh.open_sftp()
        ftp_client.put(source_path, dest_path)
        ftp_client.close()
        ssh.close()
        log.info(f"File {source_path} successfully copy to {dest_path}")
        return True
    except paramiko.AuthenticationException:
        log.error(f"Authentication failed for {host}")
        return None
    except paramiko.SSHException as e:
        log.error(f"Unable to establish SSH connection to {host}: {str(e)}")
        return None
    except TimeoutError as e:
        log.error(f"Timeout when establish SSH connection to {host}: {str(e)}")
        return None
    except Exception as e:
        log.error(f"Some error occured: {str(e)}")
        return None