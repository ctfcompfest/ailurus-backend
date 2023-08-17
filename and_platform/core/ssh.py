from os import PathLike
import os
from typing import List
from fabric import Connection, Result
import fabric
import tarfile
from and_platform.core.config import get_app_config
from secrets import token_hex

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

def copy_folder(conn: fabric.Connection, local: str, remote: str):
    tar_fname = token_hex(8)
    tar_local = os.path.join("/tmp", tar_fname)
    tar_remote = os.path.join(remote, tar_fname)

    with tarfile.open(tar_local, "w:gz") as tar:
        tar.add(local, arcname=os.path.basename(local))
    conn.put(tar_local, remote)
    os.unlink(tar_local)
    conn.run(f"tar -xz -C {remote} -f {tar_remote} && rm -f {tar_remote}")