from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import pre_load, post_dump

from .models import CheckerAgentReport

import json


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
