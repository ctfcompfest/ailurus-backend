from ailurus.models import db, Challenge, ChallengeRelease, Team, Flag
from ailurus.utils.config import set_config, get_config
from ailurus.worker.keeper.tick import tick_keeper
from ailurus.worker.keeper.flagrotator import flag_keeper
from ailurus.worker.keeper.checker import checker_keeper
from datetime import datetime, timezone, timedelta
from flask import Flask
from typing import List
from unittest.mock import patch, Mock
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


def test_tick_keeper_when_contest_not_running(app: Flask):
    with patch("ailurus.worker.keeper.tick.is_contest_running") as mock_isrun:
        mock_isrun.return_value = False
        set_config("TICK_DURATION", "4")
        set_config("NUMBER_TICK", "5")
        set_config("NUMBER_ROUND", "5")

        resp = tick_keeper(app, Mock(return_value="callback called!"), [])
        assert resp == False
        assert get_config("CURRENT_TICK") == None
        assert get_config("CURRENT_ROUND") == None

def test_tick_keeper_when_initiate_tick_noparam_callback(app: Flask):
    with patch("ailurus.worker.keeper.tick.is_contest_running") as mock_isrun:
        mock_isrun.return_value = True
        set_config("TICK_DURATION", "4")
        set_config("NUMBER_TICK", "5")
        set_config("NUMBER_ROUND", "5")

        resp = tick_keeper(app, Mock(return_value="callback called!"), [])
        assert resp == "callback called!"
        assert get_config("CURRENT_TICK") == 1
        assert get_config("CURRENT_ROUND") == 1

def test_tick_keeper_when_initiate_tick_param_callback(app: Flask):
    with patch("ailurus.worker.keeper.tick.is_contest_running") as mock_isrun:
        mock_isrun.return_value = True
        set_config("TICK_DURATION", "4")
        set_config("NUMBER_TICK", "5")
        set_config("NUMBER_ROUND", "5")

        resp = tick_keeper(app, (lambda x: x*2), [5])
        assert resp == 10
        assert get_config("CURRENT_TICK") == 1
        assert get_config("CURRENT_ROUND") == 1

def test_tick_keeper_when_double_call_less_than_tick_duration(app: Flask):
    with patch("ailurus.worker.keeper.tick.is_contest_running") as mock_isrun:
        mock_isrun.return_value = True
        set_config("TICK_DURATION", "4")
        set_config("NUMBER_TICK", "5")
        set_config("NUMBER_ROUND", "5")

        resp = tick_keeper(app, (lambda x: x*2), [5])
        assert resp == 10
        assert get_config("CURRENT_TICK") == 1
        assert get_config("CURRENT_ROUND") == 1

        resp = tick_keeper(app, (lambda x: x*2), [5])
        assert resp == False
        assert get_config("CURRENT_TICK") == 1
        assert get_config("CURRENT_ROUND") == 1

def test_tick_keeper_when_tick_reach_max(app: Flask):
    with patch("ailurus.worker.keeper.tick.is_contest_running") as mock_isrun:
        mock_isrun.return_value = True
        set_config("TICK_DURATION", "4")
        set_config("NUMBER_ROUND", "5")
        set_config("NUMBER_TICK", "5")
        set_config("CURRENT_ROUND", "2")
        set_config("CURRENT_TICK", "5")

        resp = tick_keeper(app, (lambda x: x*2), [5])
        assert resp == 10
        assert get_config("CURRENT_TICK") == 1
        assert get_config("CURRENT_ROUND") == 3

def test_flag_keeper_when_contest_not_running(app: Flask, challenge_fixture, team_fixture):
    with patch("ailurus.worker.keeper.flagrotator.is_contest_running") as mock_isrun:
        mock_isrun.return_value = False
        resp = flag_keeper(app, None)
        assert resp == False
        assert Flag.query.count() == 0

def test_flag_keeper_when_lasttick_far(app: Flask, challenge_fixture, team_fixture):
    with patch("ailurus.worker.keeper.flagrotator.is_contest_running") as mock_isrun:
        mock_isrun.return_value = True

        # No previous last tick
        resp = flag_keeper(app, None)
        assert resp == False
        assert Flag.query.count() == 0

        old_time = datetime.now(timezone.utc) - timedelta(days=1)
        set_config("LAST_TICK_CHANGE", old_time.isoformat())
        resp = flag_keeper(app, None)
        assert resp == False
        assert Flag.query.count() == 0

def test_flag_keeper_run_correctly(app: Flask, challenge_fixture, team_fixture):
    class MockFunction():
        @classmethod
        def basic_publish(cls, **kwargs):
            return True
        @classmethod
        def generate_flagrotator_task_body(cls, **kwargs):
            return {}
    
    def mock_get_svcmode_module(**kwargs):
        return MockFunction

    with patch("ailurus.worker.keeper.flagrotator.is_contest_running") as mock_isrun:
        with patch("ailurus.worker.keeper.flagrotator.get_svcmode_module") as mock_svcmode:
            mock_isrun.return_value = True
            mock_svcmode.side_effect = mock_get_svcmode_module

            set_config("FLAG_FORMAT", "flag{aaa}")
            set_config("LAST_TICK_CHANGE", datetime.now(timezone.utc).isoformat())

            resp = flag_keeper(app, MockFunction)
            assert resp == True
            assert Flag.query.count() == 4
            assert mock_svcmode.call_count == 1

            flags: List[Flag] = Flag.query.all()
            for flag in flags:
                assert flag.challenge_id in [1, 2]
                assert flag.value == "flag{aaa}"
                assert flag.round == 1
                assert flag.tick == 1


def test_checker_keeper_when_contest_not_running(app: Flask, challenge_fixture, team_fixture):
    with patch("ailurus.worker.keeper.checker.is_contest_running") as mock_isrun:
        mock_isrun.return_value = False
        resp = checker_keeper(app, None)
        assert resp == False

def test_checker_keeper_run_correctly(app: Flask, challenge_fixture, team_fixture):
    class MockFunction():
        generate_task_counter = 0

        @classmethod
        def basic_publish(cls, **kwargs):
            return True
        @classmethod
        def generate_checker_task_body(cls, **kwargs):
            MockFunction.generate_task_counter += 1
            return {}
    
    def mock_get_svcmode_module(**kwargs):
        return MockFunction

    with patch("ailurus.worker.keeper.checker.is_contest_running") as mock_isrun:
        with patch("ailurus.worker.keeper.checker.get_svcmode_module") as mock_svcmode:
            mock_isrun.return_value = True
            mock_svcmode.side_effect = mock_get_svcmode_module

            resp = checker_keeper(app, MockFunction)
            assert resp == True
            assert MockFunction.generate_task_counter == 4