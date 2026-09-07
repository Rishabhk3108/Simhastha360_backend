from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# roles: admin, field_team, volunteer
ROLE_ADMIN = "admin"
ROLE_FIELD_TEAM = "field_team"
ROLE_VOLUNTEER = "volunteer"

# volunteer application status
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    language: Mapped[str] = mapped_column(String(20), default="en")
    current_lat: Mapped[float] = mapped_column(nullable=True)
    current_lng: Mapped[float] = mapped_column(nullable=True)
    location_updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    volunteer_profile: Mapped["VolunteerProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    city_state: Mapped[str] = mapped_column(String(120), nullable=True)
    skills: Mapped[str] = mapped_column(String(255), default="")  # comma-separated
    availability_dates: Mapped[str] = mapped_column(String(255), default="")
    preferred_zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=True)
    id_proof_url: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_PENDING)
    on_duty: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="volunteer_profile")
