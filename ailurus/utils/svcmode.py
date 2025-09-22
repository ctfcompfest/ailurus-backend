from ailurus.utils.config import get_app_config

import ailurus.svcmodes
import flask
import importlib
import os
import json

def get_svcmode_module(service_mode: str):
    svcmode_dir = os.path.dirname(ailurus.svcmodes.__file__)
    package_dir = os.path.join(svcmode_dir, service_mode)
    
    spec = importlib.util.spec_from_file_location(
        f"ailurus.svcmodes.{service_mode}",
        os.path.join(package_dir, "__init__.py")
    )
    
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return mod

def load_svcmode_module(service_mode: str, app: flask.Flask):
    mod = get_svcmode_module(service_mode)
    try:
        return mod.load(app)
    except Exception as e:
        print(e)
        return None
    
def load_all_svcmode(app: flask.Flask):
    LOAD_SVCMODES = get_app_config("LOAD_SVCMODE").split(",")
    
    svcmode_dir = os.path.dirname(ailurus.svcmodes.__file__)
    for elm in os.listdir(svcmode_dir):
        if elm not in LOAD_SVCMODES:
            print(f"Module {elm} are not in list LOAD_SVCMODE. Skipping...")
            continue

        realpath = os.path.join(svcmode_dir, elm)
        cfgfile_path = os.path.join(realpath, "config.json")
        if not os.path.isdir(realpath) or \
            not os.path.exists(cfgfile_path): continue
        print("Module", elm)
        load_svcmode_module(elm, app)
