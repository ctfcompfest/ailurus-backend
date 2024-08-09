from ailurus.models import db, Challenge, ChallengeRelease, Team, Flag
from ailurus.utils.config import set_config, get_config
from ailurus.worker.keeper import tick_keeper, flag_keeper, checker_keeper
from datetime import datetime, timezone, timedelta
from flask import Flask
from typing import List
from unittest.mock import patch, Mock
import pika
import pytest

@pytest.fixture
def challenge_fixture():
    set_config("CURRENT_ROUND", "1")
    set_config("CURRENT_TICK", "1")

    challenges = [
        Challenge(slug=f"chall1", title=f"Chall 1", description="desc"),
        Challenge(slug=f"chall2", title=f"Chall 2", description="desc"),
        Challenge(slug=f"chall3", title=f"Chall 3", description="desc"),
    ]
    db.session.add_all(challenges)
    db.session.add(ChallengeRelease(round=1, challenge_id=1))
    db.session.add(ChallengeRelease(round=1, challenge_id=2))
    db.session.commit()
    return challenges

@pytest.fixture
def team_fixture():
    teams = [
        Team(name="team 1", email="team1@mail.com", password="test"),
        Team(name="team 2", email="team2@mail.com", password="test"),
    ]
    db.session.add_all(teams)
    db.session.commit()
    return teams

@patch("ailurus.worker.keeper.is_contest_running")
def test_tick_keeper_when_contest_not_running(mock_isrun, webapp: Flask):
    mock_isrun.return_value = False
    set_config("TICK_DURATION", "4")
    set_config("NUMBER_TICK", "5")
    set_config("NUMBER_ROUND", "5")
    resp = tick_keeper(webapp, Mock(return_value="callback called!"), [])
    assert resp == False
    assert get_config("CURRENT_TICK") == None
    assert get_config("CURRENT_ROUND") == None

@patch("ailurus.worker.keeper.is_contest_running")
def test_tick_keeper_when_initiate_tick_noparam_callback(mock_isrun, webapp: Flask):
    mock_isrun.return_value = True
    set_config("TICK_DURATION", "4")
    set_config("NUMBER_TICK", "5")
    set_config("NUMBER_ROUND", "5")
    resp = tick_keeper(webapp, Mock(return_value="callback called!"), [])
    assert resp == "callback called!"
    assert get_config("CURRENT_TICK") == 1
    assert get_config("CURRENT_ROUND") == 1

@patch("ailurus.worker.keeper.is_contest_running")
def test_tick_keeper_when_initiate_tick_param_callback(mock_isrun, webapp: Flask):
    mock_isrun.return_value = True
    set_config("TICK_DURATION", "4")
    set_config("NUMBER_TICK", "5")
    set_config("NUMBER_ROUND", "5")
    resp = tick_keeper(webapp, (lambda x: x*2), [5])
    assert resp == 10
    assert get_config("CURRENT_TICK") == 1
    assert get_config("CURRENT_ROUND") == 1

@patch("ailurus.worker.keeper.is_contest_running")
def test_tick_keeper_when_double_call_less_than_tick_duration(mock_isrun, webapp: Flask):
    mock_isrun.return_value = True
    set_config("TICK_DURATION", "4")
    set_config("NUMBER_TICK", "5")
    set_config("NUMBER_ROUND", "5")

    resp = tick_keeper(webapp, (lambda x: x*2), [5])
    assert resp == 10
    assert get_config("CURRENT_TICK") == 1
    assert get_config("CURRENT_ROUND") == 1

    resp = tick_keeper(webapp, (lambda x: x*2), [5])
    assert resp == False
    assert get_config("CURRENT_TICK") == 1
    assert get_config("CURRENT_ROUND") == 1

@patch("ailurus.worker.keeper.is_contest_running")
def test_tick_keeper_when_tick_reach_max(mock_isrun, webapp: Flask):
    mock_isrun.return_value = True
    set_config("TICK_DURATION", "4")
    set_config("NUMBER_ROUND", "5")
    set_config("NUMBER_TICK", "5")
    set_config("CURRENT_ROUND", "2")
    set_config("CURRENT_TICK", "5")

    resp = tick_keeper(webapp, (lambda x: x*2), [5])
    assert resp == 10
    assert get_config("CURRENT_TICK") == 1
    assert get_config("CURRENT_ROUND") == 3

@patch("ailurus.worker.keeper.is_contest_running")
def test_flag_keeper_when_contest_not_running(mock_isrun, webapp: Flask, challenge_fixture, team_fixture):
    mock_isrun.return_value = False
    resp = flag_keeper(webapp)
    assert resp == False
    assert Flag.query.count() == 0

@patch("ailurus.worker.keeper.is_contest_running")
def test_flag_keeper_when_lasttick_far(mock_isrun, webapp: Flask, challenge_fixture, team_fixture):
    mock_isrun.return_value = True
    # No previous last tick
    resp = flag_keeper(webapp)
    assert resp == False
    assert Flag.query.count() == 0

    old_time = datetime.now(timezone.utc) - timedelta(days=1)
    set_config("LAST_TICK_CHANGE", old_time.isoformat())
    resp = flag_keeper(webapp)
    assert resp == False
    assert Flag.query.count() == 0

@patch("ailurus.worker.keeper.is_contest_running")
@patch("ailurus.worker.keeper.pika")
def test_flag_keeper_run_correctly(mock_pika, mock_isrun, webapp: Flask, challenge_fixture, team_fixture):
    mock_queue = Mock(pika.channel.Channel)
    mock_pikacon = Mock()
    mock_pikacon.channel.return_value = mock_queue
    mock_pika.BlockingConnection.return_value = mock_pikacon

    mock_isrun.return_value = True

    set_config("FLAG_FORMAT", "flag{aaa}")
    set_config("LAST_TICK_CHANGE", datetime.now(timezone.utc).isoformat())

    resp = flag_keeper(webapp)
    assert resp == True
    assert Flag.query.count() == 4
    assert mock_queue.basic_publish.call_count == 4
    
    flags: List[Flag] = Flag.query.all()
    for flag in flags:
        assert flag.challenge_id in [1, 2]
        assert flag.value == "flag{aaa}"
        assert flag.round == 1
        assert flag.tick == 1


@patch("ailurus.worker.keeper.is_contest_running")
def test_checker_keeper_when_contest_not_running(mock_isrun, webapp: Flask, challenge_fixture, team_fixture):
    mock_isrun.return_value = False
    resp = checker_keeper(webapp)
    assert resp == False

@patch("ailurus.worker.keeper.is_contest_running")
@patch("ailurus.worker.keeper.pika")
def test_checker_keeper_run_correctly(mock_pika, mock_isrun, webapp: Flask, challenge_fixture, team_fixture):
    mock_queue = Mock(pika.channel.Channel)
    mock_pikacon = Mock()
    mock_pikacon.channel.return_value = mock_queue
    mock_pika.BlockingConnection.return_value = mock_pikacon

    mock_isrun.return_value = True

    resp = checker_keeper(webapp)
    assert resp == True
    assert mock_queue.basic_publish.call_count == 4
    