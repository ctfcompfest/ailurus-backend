from importlib.machinery import SourceFileLoader
from types import ModuleType
import ailurus.svcmodes
import os
import sys

import importlib

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