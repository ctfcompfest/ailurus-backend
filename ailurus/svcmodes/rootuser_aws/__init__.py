from ailurus.models import db, Team, Challenge, Service, CheckerResult, CheckerStatus, Flag, ChallengeRelease, Submission
from ailurus.schema import ServiceSchema, FlagSchema
from ailurus.utils.config import get_config, get_app_config
from functools import cmp_to_key
from sqlalchemy import select, func
from typing import List, Dict, Mapping, Any

from .svcmanager import do_provision, do_reset, do_restart
from .schema import CheckerTask, FlagrotatorTask, ServiceManagerTask, TeamLeaderboardEntry, TeamChallengeLeaderboardEntry

import base64
import datetime
import flask
import importlib
import json
import logging
import os
import pika
import requests
import zipfile

from multiprocessing import TimeoutError
from multiprocessing.pool import ThreadPool

log = logging.getLogger(__name__)

def generator_public_services_info(team: Team, challenge: Challenge, services: List[Service]) -> Dict | List | str:
    """
    Service detail format:
    {
        "publish": {
            "IP": "1.2.3.4",
            "Username": "root",
            "Password": "password",
        },
        "admin": {...}
    }
    """
    return json.loads(services[0].detail).get("publish", {}).get("IP", "")

def generator_public_services_status_detail(result_detail: Mapping[str, Any]) -> Dict | List | str:
    if result_detail.get("checker_output"):
        return result_detail["checker_output"]
    if result_detail.get("is_timeout"):
        return "Timeout"
    return "Unknown"

def calculate_team_chall_leaderboard_entry(team_id: int, chall_id: int, freeze_time: datetime.datetime):
    result: TeamChallengeLeaderboardEntry = {}
    flag_captured = db.session.execute(
        select(func.count(Submission.id)).join(Flag, Flag.id == Submission.flag_id).where(
            Submission.verdict == True,
            Submission.team_id == team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
            Flag.team_id != team_id,
        )
    ).scalar()
    flag_stolen = db.session.execute(
        select(func.count(Submission.id)).join(Flag, Flag.id == Submission.flag_id).where(
            Submission.verdict == True,
            Submission.team_id != team_id,
            Submission.challenge_id == chall_id,
            Submission.time_created <= freeze_time,
            Flag.team_id == team_id,
        )
    ).scalar()
    checker_valid = db.session.execute(
        select(func.count(CheckerResult.id)).where(
            CheckerResult.challenge_id == chall_id,
            CheckerResult.team_id == team_id,
            CheckerResult.status == CheckerStatus.VALID,
            CheckerResult.time_created <= freeze_time,
        )
    ).scalar()
    checker_faulty = db.session.execute(
        select(func.count(CheckerResult.id)).where(
            CheckerResult.challenge_id == chall_id,
            CheckerResult.team_id == team_id,
            CheckerResult.status == CheckerStatus.FAULTY,
            CheckerResult.time_created <= freeze_time,
        )
    ).scalar()
    
    result["flag_captured"] = flag_captured
    result["flag_stolen"] = flag_stolen
    result["attack"] = flag_captured
    result["defend"] = -0.5 * flag_stolen
    result["sla"] = 100
    if (checker_valid + checker_faulty) != 0:
        result["sla"] = checker_valid / (checker_valid + checker_faulty) * 100
    return result

def get_leaderboard(freeze_time: datetime.datetime | None = None, is_admin: bool = False) -> List:
    results: List[TeamLeaderboardEntry] = []

    if is_admin or freeze_time == None:
        freeze_time = datetime.datetime.now(datetime.timezone.utc)

    current_round = get_config("CURRENT_ROUND")
    chall_ids: List[int] = db.session.execute(
        select(ChallengeRelease.challenge_id).where(ChallengeRelease.round <= current_round).distinct(ChallengeRelease.challenge_id)
    ).scalars().all()
    teams: List[Team] = Team.query.all()

    for team in teams:
        team_leaderboard_entry: TeamLeaderboardEntry = {
            "team_id": team.id,
            "team_name": team.name,
            "challenges": {},
            "total_score": 0,
        }
        for chall_id in chall_ids:
            chall_entry = calculate_team_chall_leaderboard_entry(team.id, chall_id, freeze_time)
            team_leaderboard_entry["challenges"][chall_id] = chall_entry
        results.append(team_leaderboard_entry)

    # Calculate total score for each team
    for team in results:
        for chall_id in chall_ids:
            chall_score = team["challenges"][chall_id]
            team["total_score"] += chall_score["attack"] + chall_score["defend"] + chall_score["sla"]

    results_sorted = sorted(results, key=cmp_to_key(lambda x, y: x["total_score"] > y["total_score"]))
    for i in range(len(results_sorted)):
        results_sorted[i]["rank"] = i + 1
    return results_sorted

def handler_svcmanager_request(**kwargs) -> flask.Response:
    ALLOWED_ACTION = ["get_credentials", "provision", "reset", "restart"]

    is_admin = kwargs.get('is_admin', False)
    if not kwargs.get('is_allow_manage', False) and not is_admin:
        return flask.jsonify(status="failed", message="failed."), 403
    request: flask.Request = kwargs.get('request')
    chall_id = kwargs.get('challenge_id')
    team_id = kwargs.get('team_id')
    
    cmd = request.args.get("action")
    if cmd not in ALLOWED_ACTION:
        return flask.jsonify(status="failed", message="invalid command."), 400
    
    if cmd == "get_credentials":
        service = Service.query.filter_by(challenge_id=chall_id, team_id=team_id).first()
        if not service:
            return flask.jsonify(status="failed", message="invalid command."), 400
        return flask.jsonify(status="success", message=json.loads(service.detail).get("publish", {}))

    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    queue_name = get_app_config("QUEUE_SVCMANAGER_TASK", "svcmanager_task")
    rabbitmq_channel.queue_declare(queue_name, durable=True)

    artifact_path = os.path.join(get_app_config("DATA_DIR"), "challenges", f"artifact-{chall_id}.zip")
    with open(artifact_path, "rb") as fp:
        artifact_data = base64.b64encode(fp.read())

    taskbody = {
        "action": cmd,
        "initiator": ("team" if not is_admin else "admin"),
        "artifact": artifact_data.decode(),
        "challenge_id": chall_id,
        "team_id": team_id,
        "time_created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    rabbitmq_channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=base64.b64encode(
            json.dumps(
                taskbody
            ).encode()
        )
    )
    rabbitmq_conn.close()
    
    return flask.jsonify(status="success", message="success.")

def execute_check_function_with_timelimit(func, func_params, timelimit: int):
    pool = ThreadPool(processes=1)
    job = pool.apply_async(func, args=func_params)
    pool.close()
    
    verdict = job.get(timelimit)
    return verdict

def handler_checker_task(body: CheckerTask, **kwargs):
    tcroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", "testcases")
    tc_zipfile = os.path.join(tcroot_folder, body["testcase_checksum"] + ".zip")
    tc_folder = os.path.join(tcroot_folder, body["testcase_checksum"])

    if not os.path.exists(tc_folder):
        os.makedirs(tcroot_folder, exist_ok=True)
        
        link_download = get_app_config("WEBAPP_URL") + f"/api/v2/worker/testcase/{body["challenge_id"]}/"
        log.info(f"tc file not found.")
        log.debug(f"downloading tc file from {link_download}.")
        
        worker_secret = get_config("WORKER_SECRET")
        response = requests.get(link_download, headers={"X-WORKER-SECRET": worker_secret})
        log.debug(f"response from webapp: {response.status_code}.")
        
        with open(tc_zipfile, 'wb') as tczip:
            tczip.write(response.content)
    
        with zipfile.ZipFile(tc_zipfile, "r") as tczip_file:
            log.debug(f"extracting tc zipfile to {tc_folder}.")
            tczip_file.extractall(tc_folder)
    
    checker_spec = importlib.util.spec_from_file_location(
        f"ailurus.worker_data.testcases.{body['testcase_checksum']}",
        os.path.join(tc_folder, "__init__.py")
    )
    checker_module = importlib.util.module_from_spec(checker_spec)
    checker_spec.loader.exec_module(checker_module)
    checker_result = CheckerResult(
        team_id = body["team_id"],
        challenge_id = body["challenge_id"],
        round = body["current_round"],
        tick = body["current_tick"],
        time_created = body["time_created"],
    )

    checker_detail_result = {}
    try:
        log.info(f"executing testcase: chall_id={body['challenge_id']}, team_id={body['team_id']}.")
        services: List[Service] = db.session.execute(
            select(Service).where(
                Service.challenge_id == body["challenge_id"],
                Service.team_id == body["team_id"]
            )
        ).scalars().all()
        flags: List[Flag] = db.session.execute(
            select(Flag).where(
                Flag.challenge_id == body["challenge_id"],
                Flag.team_id == body["team_id"],
                Flag.tick == body["current_tick"],
                Flag.round == body["current_round"],
            )
        ).scalars().all()

        result = execute_check_function_with_timelimit(
            checker_module.main,
            [
                ServiceSchema().dump(services, many=True),
                FlagSchema().dump(flags, many=True),
            ],
            body.get("time_limit", 10)
        )
        checker_detail_result["checker_output"] = result
        checker_result.status = CheckerStatus.VALID
    except TimeoutError as e:
        log.error(f"checker failed: {str(e)}.")
        checker_detail_result["is_timeout"] = True
        checker_result.status = CheckerStatus.FAULTY
    except Exception as e:
        log.error(f"checker failed: {str(e)}.")
        checker_detail_result["exception"] = str(e)
        checker_result.status = CheckerStatus.FAULTY
    
    checker_detail_result["time_finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    checker_result.detail = json.dumps(result)

    db.session.add(checker_result)
    db.session.commit()
    return True

def handler_flagrotator_task(body: FlagrotatorTask, **kwargs):
    pass

    # TODO: process this

def handler_svcmanager_task(body: ServiceManagerTask, **kwargs):
    if body["action"] == "provision" and body["initiator"] == "admin":
        return do_provision(body, **kwargs)
    elif body["action"] == "restart":
        return do_restart(body, **kwargs)
    elif body["action"] == "reset":
        return do_reset(body, **kwargs)