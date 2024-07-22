from datetime import datetime, timezone
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Double, Enum, String, Text, TIMESTAMP
from sqlalchemy import ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

import enum

db = SQLAlchemy()
migrate = Migrate()


class Config(db.Model):
    __tablename__ = "config"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)


class Team(db.Model):
    __tablename__ = "team"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password: Mapped[str]


class Challenge(db.Model):
    __tablename__ = "challenge"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str]
    description: Mapped[str]
    point: Mapped[float] = mapped_column(Double, default=1.0)
    num_service: Mapped[int] = mapped_column(default=1, doc="Number of exposed service(s).")
    artifact_checksum: Mapped[str]


class ChallengeRelease(db.Model):
    __tablename__ = "challenge_release"
    __table_args__ = (
        UniqueConstraint("round", "challenge_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    round: Mapped[int]
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    
    @classmethod
    def get_challenges_from_round(cls, current_round: int) -> List:
        chall_release = cls.query.with_entities(cls.challenge_id)\
            .filter(cls.round == int(current_round)).all()
        return [elm[0] for elm in chall_release]
    

class Flag(db.Model):
    __tablename__ = "flag"
    __table_args__ = (
        UniqueConstraint("team_id", "challenge_id", "round", "tick"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    round: Mapped[int]
    tick: Mapped[int]
    value: Mapped[str] = mapped_column(Text)


class Submission(db.Model):
    __tablename__ = "submission"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    flag_id: Mapped[int] = mapped_column(ForeignKey("flag.id"))
    round: Mapped[int]
    tick: Mapped[int]
    value: Mapped[str] = mapped_column(Text)
    verdict: Mapped[bool]
    point: Mapped[float] = mapped_column(Double, default=0.0)
    time_created: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now(timezone.utc))

class Solve(db.Model):
    __tablename__ = "solve"
    __table_args__ = (
        UniqueConstraint("team_id", "challenge_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    time_created: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now(timezone.utc))

    @classmethod
    def is_solved(cls, team_id: int, chall_id: int) -> list:
        return cls.query.filter(cls.challenge_id == chall_id, cls.team_id == team_id).count() > 0
    

class ProvisionMachine(db.Model):
    __tablename__ = "provision_machine"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    host: Mapped[str]
    port: Mapped[int]
    credential: Mapped[str] = mapped_column(Text, doc="JSON format credential configuration.")


class Service(db.Model):
    __tablename__ = "service"
    __table_args__ = (
        UniqueConstraint("team_id", "challenge_id", "order"),
        Index("service_idx", "team_id", "challenge_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    order: Mapped[int]
    secret: Mapped[str]
    detail: Mapped[str] = mapped_column(Text, doc="JSON format service detail configuration.")
    time_created: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now(timezone.utc))
    
    @classmethod
    def is_teamservice_exist(cls, team_id, challenge_id):
        return cls.query.where(cls.team_id == team_id, cls.challenge_id == challenge_id).count() > 0


class CheckerStatus(enum.IntEnum, enum.Enum):
    QUEUE = -1
    PROCESS = 99
    FAULTY = 0
    VALID = 1


class CheckerResult(db.Model):
    __tablename__ = "checker_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    round: Mapped[int]
    tick: Mapped[int]
    status: Mapped[CheckerStatus] = mapped_column(Enum(CheckerStatus), default=CheckerStatus.QUEUE)
    detail: Mapped[str] = mapped_column(Text, doc="JSON format checker result detail.")
    time_created: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now(timezone.utc))


class TeamActivityLog(db.Model):
    __tablename__ = "team_activity_log"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    team_name: Mapped[str]
    activity: Mapped[str] = mapped_column(String(32), doc="Activity log code.")
    detail: Mapped[str] = mapped_column(Text, doc="JSON format team activity log detail.")
    time_created: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now(timezone.utc))


class ScorePerTick(db.Model):
    __tablename__ = "score_per_tick"
    __table_args__ = (
        UniqueConstraint("round", "tick", "team_id", "challenge_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    round: Mapped[int]
    tick: Mapped[int]
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    attack_score: Mapped[float] = mapped_column(Double, default=0.0)
    defense_score: Mapped[float] = mapped_column(Double, default=0.0)
    sla: Mapped[float] = mapped_column(Double, default=1.0)
    time_created: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now(timezone.utc))

    team: Mapped["Team"] = relationship('Team', foreign_keys="ScorePerTick.team_id", lazy='joined')