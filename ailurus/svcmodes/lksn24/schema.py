from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import pre_load, post_dump
from typing import TypedDict, Dict

import datetime
import json

from .models import CheckerAgentReport

class ServiceManagerTaskSchema(TypedDict):
    action: str
    initiator: str
    artifact: str
    challenge_id: int
    team_id: int
    time_created: str

class ServiceDetailSchema(TypedDict):
    ServiceDetailPublish = TypedDict('ServiceDetailPublish', {'IP':str, 'Username':str, "Private Key":str})
    ServiceDetailChecker = TypedDict('ServiceDetailChecker', {'ip':str, 'username':str, 'private_key':str, 'instance_id':str})
    
    stack_name: str
    publish: ServiceDetailPublish
    checker: ServiceDetailChecker

class FlagrotatorTaskSchema(TypedDict):
    flag_value: str
    flag_order: int
    challenge_id: int
    team_id: int
    current_tick: int
    current_round: int
    time_created: str

class TeamChallengeLeaderboardEntry(TypedDict):
    flag_captured: int
    flag_stolen: int
    attack: str
    defense: str
    sla: str

class TeamLeaderboardEntry(TypedDict):
    id: int
    name: str
    rank: int
    total_score: float
    challenges: Dict[int, TeamChallengeLeaderboardEntry]

class CheckerTaskSchema(TypedDict):
    time_limit: int
    challenge_id: int
    team_id: int
    testcase_checksum: str
    artifact_checksum: str
    current_tick: int
    current_round: int
    time_created: str

class CheckerResultDetailSchema(TypedDict):
    message: str
    exception: str
    checker_output: Dict
    time_finished: datetime.datetime

class CheckerAgentReportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CheckerAgentReport
    
    @pre_load
    def dumps_status(self, data, **kwargs):
        for key in ["flag_status", "challenge_status"]:
            if key in data and isinstance(data[key], (dict, list)):
                data[key] = json.dumps(data[key])
        return data
    
    @post_dump
    def parse_status(self, data, **kwargs):
        for key in ["flag_status", "challenge_status"]:
            if key in data and isinstance(data[key], (dict, list)):
                data[key] = json.loads(data[key])
        return data