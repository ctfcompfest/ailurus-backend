from ailurus.models import db
from datetime import datetime
from sqlalchemy import TIMESTAMP, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

class ManageServicePendingList(db.Model):
    __tablename__ = 'gcpk8s_managesvc_pending_list'

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int]
    challenge_id: Mapped[int]
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    time_created: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())