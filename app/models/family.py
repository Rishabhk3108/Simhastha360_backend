from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FamilyGroup(Base):
    __tablename__ = "family_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_by_device_id: Mapped[str] = mapped_column(String(120))
    meeting_point_lat: Mapped[float] = mapped_column(nullable=True)
    meeting_point_lng: Mapped[float] = mapped_column(nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"))
    device_id: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(120))
    last_lat: Mapped[float] = mapped_column(nullable=True)
    last_lng: Mapped[float] = mapped_column(nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class FamilyShareLink(Base):
    __tablename__ = "family_share_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    device_id: Mapped[str] = mapped_column(String(120))
    revoked: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
