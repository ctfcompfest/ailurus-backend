from and_platform.models import Servers
from base64 import b64decode
from fabric import Connection, Result
from io import StringIO
from os import PathLike
from secrets import token_hex
from typing import List

import os
import paramiko
import tarfile
import re

def execute_remote_command(host: str, *cmds: List[str]) -> List[Result]:
    conn = Connection(host)

    results = []
    for cmd in cmds:
        results.append(conn.run(cmd))
    return results

def copy_file(host: str, path: PathLike, remote: PathLike):
    local_path = os.fspath(path)
    remote_path = os.fspath(remote)

    conn = Connection(host)
    return conn.put(local_path, remote=remote_path)

def create_ssh_from_server(server: Servers) -> Connection:
    sshkey_split = server.auth_key.split("\n")
    sshkey_header = sshkey_split[0]

    if sshkey_header.find("RSA") != -1:
        key_mode = "ssh-rsa"
    elif sshkey_header.find("OPENSSH") != -1:
        sshkey = "".join(sshkey_split[1:-1])
        # Find "ssh-<something>" except "ssh-key"
        key_mode = re.search(b"ssh-(?!key)[A-Za-z0-9]+", b64decode(sshkey.encode())).group(0).decode()
    
    keyfile = StringIO(server.auth_key)
    if key_mode == "ssh-ed25519":
        pkey = paramiko.Ed25519Key.from_private_key(keyfile)
    elif key_mode == "ssh-ecdsa":
        pkey = paramiko.ECDSAKey.from_private_key(keyfile)
    elif key_mode == "ssh-dss":
        pkey = paramiko.DSSKey.from_private_key(keyfile)
    elif key_mode == "ssh-rsa":
        pkey = paramiko.RSAKey.from_private_key(keyfile)
    else:
        raise ValueError(f"could not recognize {key_mode} as a key type.")
    return Connection(host=server.host, user=server.username, port=server.sshport, connect_kwargs={"pkey": pkey})

def copy_folder(conn: Connection, local: str, remote: str):
    tar_fname = token_hex(8)
    tar_local = os.path.join("/tmp", tar_fname)
    tar_remote = os.path.join(remote, tar_fname)

    conn.run(f"mkdir -p {remote}", warn=True, hide=True)
    with tarfile.open(tar_local, "w:gz") as tar:
        tar.add(local, arcname=os.path.basename(local))
    conn.put(tar_local, remote)
    os.unlink(tar_local)
    conn.run(f"tar -xz -C {remote} -f {tar_remote} && rm -f {tar_remote}", warn=True, hide=True)