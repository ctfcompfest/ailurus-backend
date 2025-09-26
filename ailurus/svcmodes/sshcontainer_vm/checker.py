from ailurus.models import CheckerAgentReport, db, Flag, Service, CheckerResult, CheckerStatus
from ailurus.schema import CheckerAgentReportSchema, FlagSchema, ServiceSchema
from ailurus.utils.checker import execute_check_function_with_timelimit

from .types import CheckerTaskType, CheckerResultDetailType
from .utils import init_challenge_asset

import datetime
import importlib
import json
import logging
import os
import traceback
from sqlalchemy import select
from typing import List

log = logging.getLogger(__name__)

def handler_checker_task(body: CheckerTaskType, **kwargs):
    if not body["testcase_checksum"]:
        return False
    tc_folder = init_challenge_asset(
        body["challenge_id"],
        body["testcase_checksum"],
        "testcase",
    )

    checker_spec = importlib.util.spec_from_file_location(
        "ailurus.worker_data.testcases.{}".format(body["testcase_checksum"]),
        os.path.join(tc_folder, "__init__.py"),
    )
    checker_module = importlib.util.module_from_spec(checker_spec)
    checker_spec.loader.exec_module(checker_module)
    checker_result = CheckerResult(
        team_id=body["team_id"],
        challenge_id=body["challenge_id"],
        round=body["current_round"],
        tick=body["current_tick"],
    )

    checker_detail_result: CheckerResultDetailType = {}
    try:
        log.info(
            "executing testcase: chall_id={}, team_id={}.".format(
                body["challenge_id"], body["team_id"]
            )
        )
        services: List[Service] = (
            db.session.execute(
                select(Service).where(Service.team_id == body["team_id"])
            )
            .scalars()
            .all()
        )
        flags: List[Flag] = (
            db.session.execute(
                select(Flag).where(
                    Flag.challenge_id == body["challenge_id"],
                    Flag.team_id == body["team_id"],
                    Flag.tick == body["current_tick"],
                    Flag.round == body["current_round"],
                )
            )
            .scalars()
            .all()
        )

        agent_latest_report: CheckerAgentReport = (
            CheckerAgentReport.query.filter_by(
                challenge_id=body["challenge_id"], team_id=body["team_id"]
            )
            .order_by(CheckerAgentReport.time_created.desc())
            .first()
        )

        checker_status, checker_detail = execute_check_function_with_timelimit(
            checker_module.main,
            [
                ServiceSchema().dump(services, many=True),
                FlagSchema().dump(flags, many=True),
                CheckerAgentReportSchema().dump(agent_latest_report),
            ],
            body.get("time_limit", 10),
        )

        checker_detail_result["checker_output"] = checker_detail
        checker_detail_result["status_detail"] = checker_detail["status_detail"]
        checker_result.status = (
            CheckerStatus.VALID if checker_status else CheckerStatus.FAULTY
        )
    except TimeoutError as e:
        log.error(f"checker failed: {str(e)}.")
        checker_detail_result["status_detail"] = "not reachable"
        checker_result.status = CheckerStatus.FAULTY
    except Exception as e:
        log.error(f"checker failed: {str(e)}.")
        log.error("{}", traceback.format_exc())
        checker_detail_result["status_detail"] = "internal error"
        checker_detail_result["exception"] = str(e)
        checker_result.status = CheckerStatus.FAULTY

    checker_detail_result["time_finished"] = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()
    checker_result.detail = json.dumps(checker_detail_result)

    db.session.add(checker_result)
    db.session.commit()
    return True
