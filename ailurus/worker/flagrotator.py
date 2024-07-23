from ailurus.utils.config import get_config
from flask import Flask
from importlib.machinery import SourceFileLoader

import ailurus.svcmodes
import os

def rotate_flag(current_tick: int, current_round: int, app: Flask):
    with app.app_context():
        service_mode = get_config("SERVICE_MODE")
        svcmode_dir = os.path.dirname(ailurus.svcmodes.__file__)
        package_dir = os.path.join(svcmode_dir, service_mode)
        
        rotator_adapter = SourceFileLoader(f"{service_mode}.flagrotator", os.path.join(package_dir, "flagrotator.py")).load_module()
        return rotator_adapter.rotate_flag(current_tick, current_round, app)