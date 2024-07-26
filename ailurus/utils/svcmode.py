from importlib.machinery import SourceFileLoader
import ailurus.svcmodes
import os

def get_svcmode_module(service_mode: str):
    svcmode_dir = os.path.dirname(ailurus.svcmodes.__file__)
    package_dir = os.path.join(svcmode_dir, service_mode)
        
    return SourceFileLoader(
        f"ailurus.svcmodes.{service_mode}",
        os.path.join(package_dir, "__init__.py")
    ).load_module()
