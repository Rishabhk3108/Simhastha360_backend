from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

VEHICLE_TWO_WHEELER = "two_wheeler"
VEHICLE_THREE_WHEELER = "three_wheeler"
VEHICLE_FOUR_WHEELER = "four_wheeler"
VEHICLE_SIX_WHEELER = "six_wheeler"
VEHICLE_TYPES = [VEHICLE_TWO_WHEELER, VEHICLE_THREE_WHEELER, VEHICLE_FOUR_WHEELER, VEHICLE_SIX_WHEELER]


class ParkingZone(Base):
    __tablename__ = "parking_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    center_lat: Mapped[float] = mapped_column()
    center_lng: Mapped[float] = mapped_column()
    capacity_two_wheeler: Mapped[int] = mapped_column(default=0)
    capacity_three_wheeler: Mapped[int] = mapped_column(default=0)
    capacity_four_wheeler: Mapped[int] = mapped_column(default=0)
    capacity_six_wheeler: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class ParkingBooking(Base):
    __tablename__ = "parking_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parking_zone_id: Mapped[int] = mapped_column(ForeignKey("parking_zones.id"))
    vehicle_type: Mapped[str] = mapped_column(String(20))
    vehicle_number: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
