from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

db = SQLAlchemy()
migrate = Migrate()


class Team(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, index=True, unique=True)
    password = sa.Column(sa.String)
