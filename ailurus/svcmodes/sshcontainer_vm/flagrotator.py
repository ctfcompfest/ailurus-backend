from ailurus.models import Team, Challenge, Service
from ailurus.utils.config import get_config, get_app_config
from typing import List, Dict, Mapping, Any

import datetime
import flask
import json
import os
import secrets
import time

def handler_flagrotator_task(body: Mapping[str, Any], **kwargs):
    time.sleep(5)
    destfolder = os.path.join(get_app_config("DATA_DIR"), "unittest")
    os.makedirs(destfolder, exist_ok=True)    
    logfile = os.path.join(destfolder, "flag-" + secrets.token_hex(6))
    with open(logfile, "w+") as f:
        f.write(json.dumps(body))
    return get_config("CURRENT_ROUND")
