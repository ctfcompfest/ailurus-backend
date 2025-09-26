from ailurus.models import (
    CheckerAgentReport,
    Team,
    Service,
    Submission,
    ProvisionMachine,
    Flag,
    CheckerResult,
    CheckerStatus,
    Challenge,
    ChallengeRelease,
)
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import pre_load, post_dump, fields
from werkzeug.security import generate_password_hash
from marshmallow.exceptions import ValidationError
from typing import TypedDict

import json

class EnumField(fields.Field):
    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return value.value

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return self.enum(value)
        except ValueError:
            raise ValidationError(f"Invalid value for {self.enum.__name__}: {value}")

class TeamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Team
        load_instance = True

    password = auto_field(load_only=True)

    @pre_load
    def hash_password(self, data, **kwargs):
        if 'password' in data:
            data['password'] = generate_password_hash(data["password"])
        return data

class TeamPublicSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Team

    @post_dump
    def delete_sensitive_data(self, data, **kwargs):
        del data['password']
        del data['email']
        return data        
    

class SubmissionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Submission
        load_instance = True
        include_fk = True

class ServiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        load_instance = True
        include_fk = True
    @pre_load
    def dumps_detail(self, data, **kwargs):
        if 'detail' in data and isinstance(data['detail'], (dict, list)):
            data['detail'] = json.dumps(data['detail'])
        return data
    
    @post_dump
    def parse_detail(self, data, **kwargs):
        data['detail'] = json.loads(data['detail'])
        return data

class ProvisionMachineSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ProvisionMachine
        load_instance = True
    
    @pre_load
    def dumps_detail(self, data, **kwargs):
        if 'detail' in data and isinstance(data['detail'], (dict, list)):
            data['detail'] = json.dumps(data['detail'])
        return data

    @post_dump
    def parse_detail(self, data, **kwargs):
        data['detail'] = json.loads(data['detail'])
        return data

class CheckerResultSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CheckerResult
        load_instance = True
        include_fk = True
    
    status = EnumField(CheckerStatus, required=True)
    
    @pre_load
    def dumps_detail(self, data, **kwargs):
        if 'detail' in data and isinstance(data['detail'], (dict, list)):
            data['detail'] = json.dumps(data['detail'])
        return data
    
    @post_dump
    def parse_detail(self, data, **kwargs):
        data['detail'] = json.loads(data['detail'])
        return data
    
class CheckerAgentReportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CheckerAgentReport

    @pre_load
    def dumps_report(self, data, **kwargs):
        if "report" in data and isinstance(data["report"], (dict, list)):
            data["report"] = json.dumps(data["report"])
        return data

    @post_dump
    def parse_report(self, data, **kwargs):
        data["report"] = json.loads(data["report"])
        return data

class ChallengeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Challenge
        load_instance = True

    @pre_load
    def remove_generated_attributes(self, data, **kwargs):
        exclude_attrs = ["visibility", "artifact_checksum", "testcase_checksum"]
        for attr in exclude_attrs:
            if attr in data:
                del data[attr]
        return data
    
    @post_dump
    def add_visibility(self, data, **kwargs):
        if "id" in data:
            data['visibility'] = ChallengeRelease.get_rounds_from_challenge(data['id'])
        return data

class FlagSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Flag
    
class CheckerTaskType(TypedDict):
    time_limit: int
    challenge_id: int
    challenge_slug: str
    team_id: int
    testcase_checksum: str
    artifact_checksum: str
    current_tick: int
    current_round: int
    time_created: str
