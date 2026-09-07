from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

SOS_PENDING = "pending"
SOS_RESPONDING = "responding"
SOS_RESOLVED = "resolved"

LOST_OPEN = "open"
LOST_MATCHED = "matched"
LOST_RESOLVED = "resolved"


class SOSAlert(Base):
    __tablename__ = "sos_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(120), index=True)
    lat: Mapped[float] = mapped_column()
    lng: Mapped[float] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default=SOS_PENDING)
    assigned_responder_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class LostPersonReport(Base):
    __tablename__ = "lost_person_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_device_id: Mapped[str] = mapped_column(String(120), index=True)
    subject_name: Mapped[str] = mapped_column(String(120))
    subject_age: Mapped[int] = mapped_column(Integer, nullable=True)
    subject_photo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    last_seen_lat: Mapped[float] = mapped_column(nullable=True)
    last_seen_lng: Mapped[float] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=LOST_OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
