from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# facility types
TYPE_MEDICAL = "medical"
TYPE_TOILET = "toilet"
TYPE_WATER = "water"
TYPE_HELP_DESK = "help_desk"
TYPE_PARKING = "parking"


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(20), index=True)
    lat: Mapped[float] = mapped_column()
    lng: Mapped[float] = mapped_column()
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
