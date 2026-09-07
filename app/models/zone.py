from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

CROWD_GREEN = "green"
CROWD_YELLOW = "yellow"
CROWD_RED = "red"


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    center_lat: Mapped[float] = mapped_column()
    center_lng: Mapped[float] = mapped_column()
    crowd_level: Mapped[str] = mapped_column(String(10), default=CROWD_GREEN)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
