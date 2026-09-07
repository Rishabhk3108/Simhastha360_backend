from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

TASK_UNASSIGNED = "unassigned"
TASK_ACKNOWLEDGED = "acknowledged"
TASK_IN_PROGRESS = "in_progress"
TASK_COMPLETE = "complete"

PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(500))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=True)
    priority: Mapped[str] = mapped_column(String(10), default=PRIORITY_MEDIUM)
    status: Mapped[str] = mapped_column(String(20), default=TASK_UNASSIGNED, index=True)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    ack_deadline_minutes: Mapped[int] = mapped_column(Integer, default=15)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
