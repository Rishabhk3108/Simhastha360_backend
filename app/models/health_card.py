from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HealthCard(Base):
    __tablename__ = "health_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    emergency_contact: Mapped[str] = mapped_column(String(20))
    allergies: Mapped[str] = mapped_column(String(500), nullable=True)
    conditions: Mapped[str] = mapped_column(String(500), nullable=True)
    blood_group: Mapped[str] = mapped_column(String(10), nullable=True)
    qr_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
