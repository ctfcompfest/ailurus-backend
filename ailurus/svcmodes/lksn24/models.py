from ailurus.models import db
from datetime import datetime
from sqlalchemy import Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

class CheckerAgentReport(db.Model):
    __tablename__ = 'checker_agent_report'

    id: Mapped[int] = mapped_column(primary_key=True)
    ip_source: Mapped[str]
    selinux_status: Mapped[bool]
    flag_status: Mapped[str] = mapped_column(Text, doc="JSON format detail flag status for every challenges.")
    challenge_status: Mapped[str] = mapped_column(Text, doc="JSON format detail service status for every challenges.")
    time_created: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())