from ailurus.models import db, Config
from ailurus.utils.config import is_contest_finished, is_contest_paused, is_contest_started, is_contest_running
from datetime import datetime, timezone, timedelta
from flask import Flask

def test_contest_paused_properly(webapp: Flask):
    cfg = Config(key="IS_CONTEST_PAUSED", value="true")
    db.session.add(cfg)
    db.session.commit()
    assert is_contest_paused() == True

    cfg.value = "false"
    db.session.commit()
    assert is_contest_paused() == False


def test_contest_finished(webapp: Flask):
    # Round counting start from 1
    current_round = Config(key="CURRENT_ROUND", value="2")
    number_round = Config(key="NUMBER_ROUND", value="2")
    db.session.add_all([current_round, number_round])
    db.session.commit()
    assert is_contest_finished() == False

    current_round.value = "3"
    db.session.commit()
    assert is_contest_finished() == True

def test_contest_started(webapp: Flask):
    # Round counting start from 1
    start_time = Config(key="START_TIME", value="3020-01-01T01:00:00+00:00")
    db.session.add(start_time)
    db.session.commit()
    assert is_contest_started() == False

    time_now = datetime.now(timezone.utc).replace(microsecond=0)
    start = time_now - timedelta(minutes=3)
    start_time.value = start.isoformat()
    db.session.commit()
    assert is_contest_started() == True

def test_contest_running(webapp: Flask):
    current_round = Config(key="CURRENT_ROUND", value="1")
    number_round = Config(key="NUMBER_ROUND", value="2")
    is_paused = Config(key="IS_CONTEST_PAUSED", value="false")
    start_time = Config(key="START_TIME", value="3020-01-01T01:00:00+00:00")
    db.session.add_all([current_round, number_round, is_paused, start_time])
    db.session.commit()

    # time now < start time -> not running
    assert is_contest_running() == False

    # start time < time now -> running
    time_now = datetime.now(timezone.utc).replace(microsecond=0)
    start = time_now - timedelta(minutes=3)
    start_time.value = start.isoformat()
    db.session.commit()
    assert is_contest_running() == True

    # contest paused -> not running
    is_paused.value = "true"
    db.session.commit()
    assert is_contest_running() == False

    # number round < current round -> not running
    current_round.value = "3"
    db.session.commit()
    assert is_contest_running() == False
