from and_platform.core.config import get_config
from and_platform.core.constant import CHECKER_INTERVAL
from and_platform.models import Challenges
from celery import Celery
from celery.beat import PersistentScheduler
from celery.schedules import BaseSchedule, schedule
from datetime import datetime, timedelta
from typing import Callable

class ContestScheduler(PersistentScheduler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def install_contest_entries(self, data):
        if 'contest.move-tick' in data: return
        with self.app.conf.flask_func().app_context():
            entries = {}
            entries['contest.move-tick'] = {
                'task': 'and_platform.core.contest.move_tick',
                'schedule': schedule(run_every=timedelta(seconds=get_config("TICK_DURATION"))),
                'relative': True,
                'options': {
                    'queue':'contest',
                }
            }
            
            challenges = Challenges.query.all()
            for chall in challenges:
                schedule_name = f'checker.challenge-{chall.id}'
                entries[schedule_name] = {
                    "name": schedule_name,
                    "task": 'and_platform.checker.run_checker_for_challenge',
                    "args": (chall.id, ),
                    "schedule": schedule(run_every=CHECKER_INTERVAL, relative=True),
                    "relative": True,
                    "options": {
                        'queue':'checker',
                    }
                }
        self.update_from_dict(entries)

    def apply_entry(self, entry, producer=None):
        super().apply_entry(entry, producer)
        if entry.name == 'contest.start':
            self.install_contest_entries(self.get_schedule())


class ContestStartSchedule(BaseSchedule):
    def __init__(self, exec_datetime: datetime, nowfun: Callable | None = None, app: Celery | None = None):
        super().__init__(nowfun=nowfun, app=app)
        self.exec_datetime = self.maybe_make_aware(exec_datetime)
        self.is_triggered = False

    def remaining_estimate(self, last_run_at: datetime) -> timedelta:
        time_now = self.now()
        if time_now > self.exec_datetime:
            if not self.is_triggered:
                return timedelta(seconds=0)
            return timedelta(days=999)
        return min(self.exec_datetime - time_now, timedelta(minutes=5))

    def is_due(self, last_run_at: datetime) -> tuple[bool, datetime]:
        time_now = self.now()
        next_check = self.remaining_estimate(None).total_seconds()
        if not self.is_triggered and time_now >= self.exec_datetime:
            self.is_triggered = True
            return (True, next_check)
        else:
            return (False, next_check)