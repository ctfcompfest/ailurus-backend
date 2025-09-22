from ailurus.models import db, Service, CheckerResult, CheckerStatus, Flag
from ailurus.schema import ServiceSchema, FlagSchema
from ailurus.utils.config import get_config, get_app_config
from multiprocessing import TimeoutError
from multiprocessing.pool import ThreadPool
from sqlalchemy import select
from typing import List, Mapping, Any, Dict

from .schema import CheckerTaskSchema, CheckerResultDetailSchema, CheckerAgentReportSchema
from .models import CheckerAgentReport

import datetime
import importlib
import json
import logging
import os
import requests
import zipfile
import traceback

log = logging.getLogger(__name__)

def generator_public_services_status_detail(result_detail: CheckerResultDetailSchema) -> Dict | List | str:
    return result_detail["message"]

def handler_checker_task(body: CheckerTaskSchema, **kwargs):
    if not body["testcase_checksum"]:
        return False
    tcroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", "testcases")
    tc_zipfile = os.path.join(tcroot_folder, body["testcase_checksum"] + ".zip")
    tc_folder = os.path.join(tcroot_folder, body["testcase_checksum"])

    if not os.path.exists(tc_folder):
        os.makedirs(tcroot_folder, exist_ok=True)
        
        link_download = get_app_config("WEBAPP_URL") + "/api/v2/worker/testcase/{}/".format(body["challenge_id"])
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
        "ailurus.worker_data.testcases.{}".format(body['testcase_checksum']),
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

    checker_detail_result: CheckerResultDetailSchema = {}
    try:
        log.info("executing testcase: chall_id={}, team_id={}.".format(body['challenge_id'], body['team_id']))
        services: List[Service] = db.session.execute(
            select(Service).where(
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

        service_ip = ServiceSchema().dump(services[0])["detail"]["checker"]["ip"]
        agent_latest_report: CheckerAgentReport = CheckerAgentReport.query.filter_by(
                ip_source=service_ip
            ).order_by(CheckerAgentReport.time_created.desc()).first()

        checker_status, checker_detail = execute_check_function_with_timelimit(
            checker_module.main,
            [
                ServiceSchema().dump(services, many=True),
                FlagSchema().dump(flags, many=True),
                CheckerAgentReportSchema().dump(agent_latest_report),
            ],
            body.get("time_limit", 10)
        )

        checker_detail_result["checker_output"] = checker_detail
        checker_detail_result["message"] = checker_detail["message"]
        checker_result.status = CheckerStatus.VALID if checker_status else CheckerStatus.FAULTY
    except TimeoutError as e:
        log.error(f"checker failed: {str(e)}.")
        checker_detail_result["message"] = "not reachable"
        checker_result.status = CheckerStatus.FAULTY
    except Exception as e:
        log.error(f"checker failed: {str(e)}.")
        log.error("{}", traceback.format_exc())
        checker_detail_result["message"] = "internal error"
        checker_detail_result["exception"] = str(e)
        checker_result.status = CheckerStatus.FAULTY
    
    checker_detail_result["time_finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    checker_result.detail = json.dumps(checker_detail_result)

    db.session.add(checker_result)
    db.session.commit()
    return True

def execute_check_function_with_timelimit(func, func_params, timelimit: int):
    pool = ThreadPool(processes=1)
    job = pool.apply_async(func, args=func_params)
    pool.close()
    
    verdict = job.get(timelimit)
    return verdict
