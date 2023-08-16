import datetime
import fnmatch
import hashlib
import os
import sys
import subprocess
import tarfile
import yaml
from pathlib import Path

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
VALID_CMD = ["start", "stop", "restart", "reset", "check_patch", "apply_patch"]

PATCH_TARFILE = "patch/service.patch"
PATCH_TARPATH = os.path.join(BASE_PATH, PATCH_TARFILE)

class PatchInvalidException(Exception):
    """Exception for invalid patch file"""

def get_md5sum(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def read_patchrule():
    with open(os.path.join(BASE_PATH, "patchrule.yml")) as patchrule_file:
        return yaml.safe_load(patchrule_file)

def update_service_meta(job, **kwargs):
    with open(os.path.join(BASE_PATH, "meta.yml"), "rw") as meta_file:
        meta_data = yaml.safe_load(meta_file)
        meta_data[f"last_{job}"] = datetime.datetime.now().isoformat()
        if len(kwargs) > 0:
            for k, v in kwargs.items():
                meta_data[k] = v
        yaml.dump(meta_data, meta_file)

def start_service():
    subprocess.check_output('docker compose up --build -d', cwd=BASE_PATH)
    print('[+] service started')

def stop_service():
    subprocess.check_output('docker compose down --volume --timeout 3', cwd=BASE_PATH)
    print('[+] service stopped')

def restart_service():
    subprocess.check_output('docker compose restart --timeout 3', cwd=BASE_PATH)
    print('[+] service restarted')
    update_service_meta("restart")

def reset_service():
    stop_service()
    print('[+] service resetted')
    start_service()
    update_service_meta("reset")

def path_matching(patches, rules, f = lambda x: x):
    ptrn_path = []
    for svc, paths in rules.items():
        expand_rule = [Path(f"/{svc}{p}").resolve() for p in paths]
        ptrn_path += expand_rule
    for realpath in patches:
        is_valid = False
        for ptrn in ptrn_path:
            stt = fnmatch.fnmatch(realpath.as_posix(), ptrn.as_posix()) \
                or (ptrn in realpath.parents)
            if f(stt):
                is_valid = True
                break
        if not is_valid:
            raise PatchInvalidException(realpath.as_posix()[1:])  
    return True

def check_patch_service():
    print("[*] checking patch")
    patchrule = read_patchrule()

    try:
        with tarfile.open(PATCH_TARPATH, "r") as patch_file:
            file_list = sorted(patch_file.getnames(), reverse=True)
        leaf_list = [Path(f"/{file_list[0]}").resolve()]
        for elm in file_list:
            if elm.startswith("/"):
                raise PatchInvalidException(elm)
            elm_path = Path(f"/{elm}").resolve()
            if elm_path not in leaf_list[-1].parents:
                leaf_list.append(elm_path)

        path_matching(leaf_list, patchrule["whitelist"])
        path_matching(leaf_list, patchrule["blacklist"], lambda x: not(x))
    except PatchInvalidException as e:
        print(f"[-] {e} is not a valid patching path.")
        return False
    except Exception as e:
        print("[-] failed processing patch file.")
        return False

    print("[+] patch is valid.")
    return True

def apply_patch_service():
    service_list = read_patchrule()["whitelist"]
    
    print(f'[*] applying patch')
    for svc in service_list:
        subprocess.check_output(f'docker compose exec -d {svc} sh /.adce_patch/apply_patch.sh {svc}', cwd=BASE_PATH)
        print(f'   ... {svc} done')
    print('[+] patch applied')

    update_service_meta("patch", applied_patch=get_md5sum(PATCH_TARPATH))

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("""usage: python3 manage.py <command>\n\nAvailable command: start, stop, restart, reset, check_patch, apply_patch""")
        exit(1)
    
    command = sys.argv[1]
    if command in VALID_CMD:
        globals()[f"{command}_service"]()
    else:
        print("Invalid command")
        exit(1)