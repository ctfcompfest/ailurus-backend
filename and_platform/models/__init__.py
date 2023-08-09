from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

import enum
import secrets
import sqlalchemy as sa

db = SQLAlchemy()
migrate = Migrate()

class Configs(db.Model):
    __tablename__ = "configs"
    
    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String(128), unique=True, index=True)
    value = sa.Column(sa.Text)

class Servers(db.Model):
    __tablename__ = "servers"
    
    id = sa.Column(sa.Integer, primary_key=True)
    host = sa.Column(sa.String(50), unique=True)
    sshport = sa.Column(sa.Integer)
    username = sa.Column(sa.String(50))
    auth_key = sa.Column(sa.Text)

class Teams(db.Model):
    __tablename__ = "teams"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(128))
    email = sa.Column(sa.String(128), unique=True, index=True)
    password = sa.Column(sa.String)
    server_id = sa.Column(sa.Integer, sa.ForeignKey("servers.id"), unique=True)
    server_host = sa.Column(sa.String)
    secret = sa.Column(sa.String(50), default=secrets.token_urlsafe(32))

    score_per_ticks = sa.relationship("ScorePerTicks", back_populates="team_id", lazy=True)

class Challenges(db.Model):
    __tablename__ = "challenges"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80))
    description = sa.Column(sa.Text)
    num_expose = sa.Column(sa.Integer, default=1)
    server_id = sa.Column(sa.Integer, sa.ForeignKey("servers.id"), unique=True)
    server_host = sa.Column(sa.String)

class Flags(db.Model):
    __tablename__ = "flags"
    __table_args__ = (
        sa.UniqueConstraint("team_id", "challenge_id", "round", "tick"),
    )

    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"))
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey("challenges.id"))
    round = sa.Column(sa.Integer)
    tick = sa.Column(sa.Integer)
    value = sa.Column(sa.Text, index=True)
    
class Submissions(db.Model):
    __tablename__ = "submissions"

    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"))
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey("challenges.id"))
    round = sa.Column(sa.Integer)
    tick = sa.Column(sa.Integer)
    value = sa.Column(sa.Text, index=True)
    verdict = sa.Column(sa.Boolean)

class Solves(db.Model):
    __tablename__ = "solves"
    __table_args__ = (
        sa.PrimaryKeyConstraint("team_id", "challenge_id"),
    )

    team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"))
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey("challenges.id"))

class ChallengeReleases(db.Model):
    __tablename__ = "challenge_releases"
    __table_args__ = (
        sa.PrimaryKeyConstraint("round", "challenge_id"),
    )

    round = sa.Column(sa.Integer)
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey("challenges.id"))

class ScorePerTicks(db.Model):
    __tablename__ = "score_per_ticks"
    __table_args__ = (
        sa.UniqueConstraint("round", "tick", "team_id"),
    )

    id = sa.Column(sa.Integer, primary_key=True)
    round = sa.Column(sa.Integer)
    tick = sa.Column(sa.Integer)
    team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"))
    attack_score = sa.Column(sa.Double)
    defense_score = sa.Column(sa.Double)
    sla = sa.Column(sa.Double)

class Services(db.Model):
    __tablename__ = "services"
    __table_args__ = (
        sa.UniqueConstraint("team_id", "challenge_id", "order"),
        sa.Index("service_idx", "team_id", "challenge_id"),
    )

    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"))
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey("challenges.id"))
    order = sa.Column(sa.Integer)
    address = sa.Column(sa.String(100), unique=True)

class CheckerVerdict(enum.Enum):
    QUEUE = -1
    PROCESS = 99
    FAULTY = 0
    VALID = 1

class CheckerQueues(db.Model):
    __tablename__ = "checker_queues"

    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"))
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey("challenges.id"))
    result = sa.Column(sa.Enum(CheckerVerdict))