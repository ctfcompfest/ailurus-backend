from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

import enum
import secrets

db = SQLAlchemy()
migrate = Migrate()

class Configs(db.Model):
    __tablename__ = "configs"
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, index=True)
    value = db.Column(db.Text)

class Servers(db.Model):
    __tablename__ = "servers"
    
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(50), unique=True)
    sshport = db.Column(db.Integer)
    username = db.Column(db.String(50))
    auth_key = db.Column(db.Text)

    @classmethod
    def is_exist_with_host(self, host):
        server = self.query.filter_by(host=host).first()
        return server is not None
    
    @classmethod
    def is_exist_with_id(self, id):
        server = self.query.filter_by(id=id).first()
        return server is not None

class Teams(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True, index=True)
    password = db.Column(db.String)
    server_id = db.Column(db.Integer, db.ForeignKey("servers.id"), unique=True)
    server_host = db.Column(db.String)
    secret = db.Column(db.String(50), default=secrets.token_urlsafe(32))
    server = db.relationship("Servers", foreign_keys="Teams.server_id", lazy=True)

class Challenges(db.Model):
    __tablename__ = "challenges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.Text)
    num_expose = db.Column(db.Integer, default=1)
    server_id = db.Column(db.Integer, db.ForeignKey("servers.id"), unique=True)
    server_host = db.Column(db.String)
    server = db.relationship("Servers", foreign_keys="Challenges.server_id", lazy=True)

class Flags(db.Model):
    __tablename__ = "flags"
    __table_args__ = (
        db.UniqueConstraint("team_id", "challenge_id", "round", "tick"),
    )

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), index=True)
    round = db.Column(db.Integer)
    tick = db.Column(db.Integer)
    value = db.Column(db.Text, index=True)
    
class Submissions(db.Model):
    __tablename__ = "submissions"
    __table_args__ = (
        db.Index("team_id", "flag_id", "verdict"),
    )

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))
    round = db.Column(db.Integer)
    tick = db.Column(db.Integer)
    value = db.Column(db.Text, index=True)
    verdict = db.Column(db.Boolean)
    flag_id = db.Column(db.Integer, db.ForeignKey("flags.id"), default=None)

class Solves(db.Model):
    __tablename__ = "solves"
    __table_args__ = (
        db.PrimaryKeyConstraint("team_id", "challenge_id"),
    )

    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))

class ChallengeReleases(db.Model):
    __tablename__ = "challenge_releases"
    __table_args__ = (
        db.PrimaryKeyConstraint("round", "challenge_id"),
    )

    round = db.Column(db.Integer)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))

class ScorePerTicks(db.Model):
    __tablename__ = "score_per_ticks"
    __table_args__ = (
        db.UniqueConstraint("round", "tick", "team_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer)
    tick = db.Column(db.Integer)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    attack_score = db.Column(db.Double)
    defense_score = db.Column(db.Double)
    sla = db.Column(db.Double)

    team = db.relationship("Teams", foreign_keys="ScorePerTicks.team_id", lazy="joined")

class Services(db.Model):
    __tablename__ = "services"
    __table_args__ = (
        db.UniqueConstraint("team_id", "challenge_id", "order"),
        db.Index("service_idx", "team_id", "challenge_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))
    order = db.Column(db.Integer)
    address = db.Column(db.String(100), unique=True)

    @classmethod
    def is_teamservice_exist(cls, team_id, challenge_id):
        return cls.query.where(cls.team_id == team_id, cls.challenge_id == challenge_id).count() > 0

class CheckerVerdict(enum.Enum):
    QUEUE = -1
    PROCESS = 99
    FAULTY = 0
    VALID = 1

class CheckerQueues(db.Model):
    __tablename__ = "checker_queues"

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))
    result = db.Column(db.Enum(CheckerVerdict))