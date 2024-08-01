import hashlib
from typing import IO

def _compute_md5(data: IO[bytes]):
    md5_hash = hashlib.md5()
    for byte_block in iter(lambda: data.read(4096), b""):
        md5_hash.update(byte_block)
    return md5_hash.hexdigest()

def compute_md5(file: str | IO[bytes]):
    if hasattr(file, "read"):
        return _compute_md5(file)
    else:
        with open(file, "rb") as fp:
            return _compute_md5(fp)