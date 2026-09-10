from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# pending: no eligible responder was found at all.
# assigned: auto-assigned to a responder, awaiting their acknowledgment.
# responding: the responder acknowledged and is (presumably) en route.
# resolved: done.
SOS_PENDING = "pending"
SOS_ASSIGNED = "assigned"
SOS_RESPONDING = "responding"
SOS_RESOLVED = "resolved"

# How long an assigned responder has to acknowledge before the alert is
# reassigned to the next-nearest eligible responder. There is deliberately no
# decline action for the responder - only escalation on silence.
SOS_ACK_TIMEOUT_SECONDS = 60

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
    assigned_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    tried_responder_ids: Mapped[list] = mapped_column(JSON, default=list)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
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
