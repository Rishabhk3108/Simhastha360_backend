from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# roles: admin, field_team, volunteer, volunteer_manager, guardian
ROLE_ADMIN = "admin"
ROLE_FIELD_TEAM = "field_team"
ROLE_VOLUNTEER = "volunteer"
ROLE_VOLUNTEER_MANAGER = "volunteer_manager"
ROLE_GUARDIAN = "guardian"

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
    expo_push_token: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    volunteer_profile: Mapped["VolunteerProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    city_state: Mapped[str] = mapped_column(String(120), nullable=True)
    permanent_address: Mapped[str] = mapped_column(String(255), nullable=True)
    emergency_contact_name: Mapped[str] = mapped_column(String(120), nullable=True)
    emergency_contact_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    id_proof_type: Mapped[str] = mapped_column(String(30), nullable=True)
    id_number: Mapped[str] = mapped_column(String(60), nullable=True)
    id_proof_front_doc_id: Mapped[str] = mapped_column(ForeignKey("uploaded_documents.id"), nullable=True)
    id_proof_back_doc_id: Mapped[str] = mapped_column(ForeignKey("uploaded_documents.id"), nullable=True)
    photo_doc_id: Mapped[str] = mapped_column(ForeignKey("uploaded_documents.id"), nullable=True)
    skills: Mapped[str] = mapped_column(String(255), default="")  # comma-separated
    languages: Mapped[str] = mapped_column(String(255), default="")  # comma-separated
    availability_slots: Mapped[list] = mapped_column(JSON, default=list)  # [{date, start_time, end_time}]
    prior_experience: Mapped[str] = mapped_column(Text, nullable=True)
    tshirt_size: Mapped[str] = mapped_column(String(10), nullable=True)
    organization_affiliation: Mapped[str] = mapped_column(String(120), nullable=True)
    medical_conditions: Mapped[str] = mapped_column(Text, nullable=True)
    no_criminal_record: Mapped[bool] = mapped_column(Boolean, default=False)
    code_of_conduct_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    media_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=True)
    id_proof_url: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_PENDING)
    review_note: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(nullable=True)
    on_duty: Mapped[bool] = mapped_column(Boolean, default=False)
    accepts_emergencies: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="volunteer_profile")
