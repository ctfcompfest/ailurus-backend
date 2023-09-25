from and_platform.models import Challenges, Teams
from and_platform.core.config import check_contest_is_running
import celery
import os


@celery.shared_task
def run_checker_for_service(team_id: int, challenge_id: int):
    if not check_contest_is_running():
        return

    os.system(
        f"python3 manage.py checkexec --team {team_id} --challenge {challenge_id}"
    )


@celery.shared_task
def run_checker_for_challenge(chall_id: int):
    if is_outside_contest_time():
        return

    teams = Teams.query.all()
    jobs = [run_checker_for_service.s(team.id, chall_id) for team in teams]
    celery.group(jobs)()


@celery.shared_task
def run_checker_for_team(team_id: int):
    if is_outside_contest_time():
        return

    challenges = Challenges.query.all()
    jobs = [run_checker_for_service.s(team_id, chall.id) for chall in challenges]
    celery.group(jobs)()
