import ailurus.svcmodes
import flask
import importlib
import os

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
    return mod.load(app)