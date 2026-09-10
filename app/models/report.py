from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# report types
REPORT_CROWDED = "crowded"
REPORT_TOILET_NOT_WORKING = "toilet_not_working"
REPORT_WATER_EMPTY = "water_empty"


class CrowdReport(Base):
    __tablename__ = "crowd_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))
    type: Mapped[str] = mapped_column(String(30))
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), nullable=True)
    device_id: Mapped[str] = mapped_column(String(120), index=True)
    lat: Mapped[float] = mapped_column(nullable=True)
    lng: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


# A pilgrim-submitted "something's wrong here" report - photos + optional
# description + location, triaged by the volunteer manager into a task.
ISSUE_STATUS_NEW = "new"
ISSUE_STATUS_TASK_CREATED = "task_created"
ISSUE_STATUS_DISMISSED = "dismissed"


class IssueReport(Base):
    __tablename__ = "issue_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    photo_doc_ids: Mapped[list] = mapped_column(JSON, default=list)
    lat: Mapped[float] = mapped_column(nullable=True)
    lng: Mapped[float] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ISSUE_STATUS_NEW, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
