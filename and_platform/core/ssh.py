from os import PathLike
import os
from typing import List
from fabric import Connection, Result


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
