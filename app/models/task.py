from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

TASK_UNASSIGNED = "unassigned"
TASK_ACKNOWLEDGED = "acknowledged"
TASK_IN_PROGRESS = "in_progress"
TASK_REVIEW = "review"
TASK_COMPLETE = "complete"

PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"

MIN_COMPLETION_PHOTOS = 3


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(500))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=True)
    lat: Mapped[float] = mapped_column(nullable=True)
    lng: Mapped[float] = mapped_column(nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(String(10), default=PRIORITY_MEDIUM)
    status: Mapped[str] = mapped_column(String(20), default=TASK_UNASSIGNED, index=True)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    ack_deadline_minutes: Mapped[int] = mapped_column(Integer, default=15)
    completion_photo_doc_ids: Mapped[list] = mapped_column(JSON, default=list)
    review_note: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
