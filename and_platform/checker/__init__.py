from and_platform.core.config import get_config
from and_platform.core.constant import CHECKER_INTERVAL
from and_platform.core.ssh import create_ssh_from_server
from and_platform.core.service import get_remote_service_path
from and_platform.core.service import get_challenges_dir_fromid
from and_platform.models import db, Challenges, Teams, Servers, Services, CheckerQueues, CheckerVerdict
from fulgens import ChallengeHelper, Verdict
from importlib.machinery import SourceFileLoader
from multiprocessing import Pool
import celery

@celery.shared_task
def run_checker_for_service(team: int | Teams, challenge: int | Challenges, server: int | Servers):
    current_round = get_config("CURRENT_ROUND", 0)
    current_tick = get_config("CURRENT_TICK", 0)

    chall_id = challenge
    if isinstance(challenge, Challenges):
        chall_id = challenge.id
    if isinstance(team, int):
        team = Teams.query.filter(Teams.id == team).scalar()
    if isinstance(server, int):
        server = Servers.query.filter(Servers.id == server).scalar()

    addresses = db.session.query(Services.address).filter(
        Services.challenge_id == chall_id,
        Services.team_id == team.id
    ).order_by(Services.order).all()

    ssh_conn = create_ssh_from_server(server)
    chall_dir = get_challenges_dir_fromid(chall_id)
    helper = ChallengeHelper(
        addresses=addresses,
        secret=team.secret,
        local_challenge_dir=chall_dir,
        remote_challenge_dir=get_remote_service_path(team.id, chall_id),
        ssh_conn=ssh_conn
    )

    test_script = SourceFileLoader("checker_test", chall_dir.as_posix()).load_module()
    pool = Pool(processes=1)

    check_process = pool.apply_async(test_script.do_check, args=(helper, ))
    pool.close()
    
    verdict: Verdict = Verdict.ERROR("empty")
    try:
        verdict = check_process.get(CHECKER_INTERVAL.total_seconds() / 3)
    except TimeoutError:
        verdict = Verdict.ERROR("timeout error")
    except Exception as ex:
        verdict = Verdict.ERROR(str(ex))

    if verdict.is_ok():
        result = CheckerVerdict.VALID
    else:
        result = CheckerVerdict.FAULTY

    checkerqueue = CheckerQueues(
        team_id = team.id,
        challenge_id = chall_id,
        round = current_round,
        tick = current_tick,
        result = result,
    )
    db.session.add(checkerqueue)
    db.session.commit()

@celery.shared_task
def run_checker_for_challenge(chall_id: int):
    server_mode = get_config("SERVER_MODE")
    challenge = Challenges.query.filter(Challenges.id == chall_id).scalar()
    teams = Teams.query.all()

    pool = Pool(processes=len(teams))
    for team in teams:
        if server_mode == "private":
            server = team.server
        elif server_mode == "sharing":
            server = challenge.server
        pool.apply_async(run_checker_for_service, args=(team, challenge, server))
    pool.close()
    pool.join()

@celery.shared_task
def run_checker_for_team(team_id: int):
    server_mode = get_config("SERVER_MODE")

    team = Teams.query.filter(Teams.id == team_id).scalar()
    challenges = Challenges.query.all()
    
    pool = Pool(processes=len(challenges))
    for challenge in challenges:
        if server_mode == "private":
            server = team.server
        elif server_mode == "sharing":
            server = challenge.server
        pool.apply_async(run_checker_for_service, args=(team, challenge, server))

    pool.close()
    pool.join()