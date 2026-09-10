from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

POI_CATEGORIES = ("temple", "ghat", "heritage", "ashram")


class PointOfInterest(Base):
    """A recommended nearby place shown to foreign visitors (temples, ghats,
    heritage sites) - seeded manually for now rather than admin-managed, see
    the icon field: places show a themed icon rather than a photo until a
    real photo pipeline exists."""

    __tablename__ = "points_of_interest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(20))
    icon: Mapped[str] = mapped_column(String(40))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
