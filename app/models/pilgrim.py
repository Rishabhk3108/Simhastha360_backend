from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
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
    # Nullable: foreign visitors (is_foreigner=True) register with just name,
    # phone, country, password and a photo - they have no Aadhar number and
    # no domestic address, so those fields simply stay empty for them.
    aadhar_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    photo_base64: Mapped[str] = mapped_column(Text, nullable=True)
    samagra_id: Mapped[str] = mapped_column(String(30), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(200), nullable=True)
    address_line2: Mapped[str] = mapped_column(String(200), nullable=True)
    city: Mapped[str] = mapped_column(String(80), nullable=True)
    state: Mapped[str] = mapped_column(String(80), nullable=True)
    pincode: Mapped[str] = mapped_column(String(12), nullable=True)
    country: Mapped[str] = mapped_column(String(80), default="India")
    is_foreigner: Mapped[bool] = mapped_column(Boolean, default=False)
    medical_history: Mapped[str] = mapped_column(Text, nullable=True)
    # Nullable now: the old "guardian info collected at registration" flow is
    # retired in favor of real guardian accounts linking to a pilgrim via a
    # QR code (see GuardianLink) - kept nullable rather than dropped so any
    # pilgrim rows created under the old flow keep their guardian record.
    guardian_id: Mapped[int] = mapped_column(ForeignKey("guardians.id"), nullable=True)
    registered_via: Mapped[str] = mapped_column(String(10), default=REGISTERED_SELF)
    last_lat: Mapped[float] = mapped_column(nullable=True)
    last_lng: Mapped[float] = mapped_column(nullable=True)
    location_updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    link_token: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    link_token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    guardian: Mapped["Guardian"] = relationship()


class GuardianLink(Base):
    """Links a real guardian account (a User with role=guardian) to a
    pilgrim, established by the guardian scanning a QR code the pilgrim
    generates from their own app. Many-to-many: one guardian can watch over
    several pilgrims, and (in principle) a pilgrim could be linked to more
    than one guardian."""

    __tablename__ = "guardian_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guardian_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    pilgrim_id: Mapped[int] = mapped_column(ForeignKey("pilgrims.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
