from and_platform.extensions import db
import sqlalchemy as sa


class Team(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, index=True, unique=True)
    password = sa.Column(sa.String)
