from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

REGISTERED_SELF = "self"
REGISTERED_BY_GUARDIAN = "guardian"


class Guardian(Base):
    __tablename__ = "guardians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    aadhar_number: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    relation_to_pilgrim: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Pilgrim(Base):
    __tablename__ = "pilgrims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20), index=True)
    aadhar_number: Mapped[str] = mapped_column(String(20))
    age: Mapped[int] = mapped_column(Integer)
    photo_base64: Mapped[str] = mapped_column(Text, nullable=True)
    samagra_id: Mapped[str] = mapped_column(String(30), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(200))
    address_line2: Mapped[str] = mapped_column(String(200), nullable=True)
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    pincode: Mapped[str] = mapped_column(String(12))
    country: Mapped[str] = mapped_column(String(80), default="India")
    medical_history: Mapped[str] = mapped_column(Text, nullable=True)
    guardian_id: Mapped[int] = mapped_column(ForeignKey("guardians.id"))
    registered_via: Mapped[str] = mapped_column(String(10), default=REGISTERED_SELF)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    guardian: Mapped["Guardian"] = relationship()
