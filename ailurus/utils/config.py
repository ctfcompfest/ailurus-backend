# Taken from https://github.com/CTFd/CTFd/blob/master/CTFd/utils/__init__.py with some modification

from ailurus.models import db, Config

from datetime import datetime, timezone
from flask import current_app as app
from enum import Enum
import json
import re

string_types = (str,)
datetime_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"

def _convert_config_value(value: str):
    if value and value.isdigit():
        return int(value)
    elif value.startswith("[") and value.endswith("]"):
        return json.loads(value)
    elif re.match(datetime_pattern, value):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif value and isinstance(value, string_types):
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            return value

def get_app_config(key: str, default=None):
    value = app.config.get(key)
    if value:
        return _convert_config_value(value)
    return default

def _get_config(key: str):
    config = db.session.execute(
        Config.__table__.select().where(Config.key == key)
    ).fetchone()

    if config and config.value:
        return _convert_config_value(config.value)
    # Flask-Caching is unable to roundtrip a value of None.
    # Return an exception so that we can still cache and avoid the db hit
    return KeyError

def get_config(key: str, default=None):
    # Convert enums to raw string values to cache better
    if isinstance(key, Enum):
        key = str(key)
    
    value = _get_config(key)
    if value is KeyError:
        return default
    else:
        return value

def set_config(key: str, value):
    config = Config.query.filter_by(key=key).first()
    if config:
        config.value = value
    else:
        config = Config(key=key, value=value)
        db.session.add(config)
    db.session.commit()

    # Convert enums to raw string values to cache better
    if isinstance(key, Enum):
        key = str(key)

    return config

def is_contest_started():
    start_time: datetime = get_config("START_TIME")
    time_now = datetime.now(timezone.utc)
    return (start_time and time_now >= start_time)

def is_contest_paused():
    is_paused: bool = get_config("IS_CONTEST_PAUSED")
    return is_paused

def is_contest_finished():
    current_round = get_config("CURRENT_ROUND", 0)
    number_round = get_config("NUMBER_ROUND", 0)
    return current_round > number_round