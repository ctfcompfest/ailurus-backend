# Taken from https://github.com/CTFd/CTFd/blob/master/CTFd/utils/__init__.py with some modification

from and_platform.cache import cache
from and_platform.models import db, Configs

from datetime import datetime
from flask import current_app as app
from enum import Enum
import re

string_types = (str,)
datetime_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"

def _convert_config_value(value: str):
    if value and value.isdigit():
        return int(value)
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

@cache.memoize()
def _get_config(key: str):
    config = db.session.execute(
        Configs.__table__.select().where(Configs.key == key)
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
    config = Configs.query.filter_by(key=key).first()
    if config:
        config.value = value
    else:
        config = Configs(key=key, value=value)
        db.session.add(config)
    db.session.commit()

    # Convert enums to raw string values to cache better
    if isinstance(key, Enum):
        key = str(key)

    return config

def check_contest_is_started():
    time_now = datetime.now().astimezone()
    start_time = get_config("START_TIME")

    if start_time and (time_now >= start_time):
        return True
    return False

def check_contest_is_finished():
    current_tick = get_config("CURRENT_TICK", 0)
    current_round = get_config("CURRENT_ROUND", 0)
    number_tick = get_config("NUMBER_TICK", 0)
    number_round = get_config("NUMBER_ROUND", 0)
    return (
        current_round >= number_round
        and
        current_tick >= number_tick
    )

def check_contest_is_running():
    return check_contest_is_started() and not check_contest_is_finished()

def check_contest_is_freeze():
    time_now = datetime.now().astimezone()
    freeze_time = get_config("FREEZE_TIME")

    if freeze_time and (time_now >= freeze_time):
        return True
    return False