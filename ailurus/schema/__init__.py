from ailurus.models import Team
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import pre_load
from werkzeug.security import generate_password_hash

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