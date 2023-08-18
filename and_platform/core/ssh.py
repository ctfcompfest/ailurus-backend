from and_platform.models import Servers
from fabric import Connection, Result
from io import StringIO
from os import PathLike
from secrets import token_hex
from typing import List

import os
import paramiko
import tarfile

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
    key_mode = server.auth_key[:server.auth_key.find("PRIVATE")-1]
    key_mode = key_mode[key_mode.find(" ")+1:]
    
    keyfile = StringIO(server.auth_key.replace(key_mode, "OPENSSH"))
    if key_mode == "ED25519":
        pkey = paramiko.Ed25519Key.from_private_key(keyfile)
    elif key_mode == "ECDSA":
        pkey = paramiko.ECDSAKey.from_private_key(keyfile)
    elif key_mode == "DSS":
        pkey = paramiko.DSSKey.from_private_key(keyfile)
    elif key_mode == "RSA" or key_mode == "OPENSSH":
        pkey = paramiko.RSAKey.from_private_key(keyfile)
    return Connection(host=server.host, user=server.username, port=server.sshport, connect_kwargs={"pkey": pkey})

def copy_folder(conn: Connection, local: str, remote: str):
    tar_fname = token_hex(8)
    tar_local = os.path.join("/tmp", tar_fname)
    tar_remote = os.path.join(remote, tar_fname)

    with tarfile.open(tar_local, "w:gz") as tar:
        tar.add(local, arcname=os.path.basename(local))
    conn.put(tar_local, remote)
    os.unlink(tar_local)
    conn.run(f"tar -xz -C {remote} -f {tar_remote} && rm -f {tar_remote}")