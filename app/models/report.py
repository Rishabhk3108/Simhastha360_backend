from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
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
