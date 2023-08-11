# Taken from https://github.com/CTFd/CTFd/blob/master/CTFd/utils/__init__.py with some modification

from and_platform.models import db, Configs
from datetime import datetime
from enum import Enum
import re

string_types = (str,)

def _get_config(key):
    datetime_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    
    config = db.session.execute(
        Configs.__table__.select().where(Configs.key == key)
    ).fetchone()

    if config and config.value:
        value = config.value
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
    # Flask-Caching is unable to roundtrip a value of None.
    # Return an exception so that we can still cache and avoid the db hit
    return KeyError

def get_config(key, default=None):
    # Convert enums to raw string values to cache better
    if isinstance(key, Enum):
        key = str(key)
    
    value = _get_config(key)
    if value is KeyError:
        return default
    else:
        return value

def set_config(key, value):
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