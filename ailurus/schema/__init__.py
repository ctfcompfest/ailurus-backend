from ailurus.models import Team, Service, Submission
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import pre_load, post_dump
from werkzeug.security import generate_password_hash

import json

class TeamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Team
        load_instance = True

    id = auto_field(dump_only=True)
    password = auto_field(load_only=True)

    @pre_load
    def hash_password(self, data, **kwargs):
        if 'password' in data:
            data['password'] = generate_password_hash(data["password"])
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
    
    @post_dump
    def parse_detail(self, data, **kwargs):
        data['detail'] = json.loads(data['detail'])
        return data