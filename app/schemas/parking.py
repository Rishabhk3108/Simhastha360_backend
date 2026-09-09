from datetime import datetime

from pydantic import BaseModel


class ParkingZoneCreate(BaseModel):
    name: str
    center_lat: float
    center_lng: float
    capacity_two_wheeler: int = 0
    capacity_three_wheeler: int = 0
    capacity_four_wheeler: int = 0
    capacity_six_wheeler: int = 0


class ParkingZoneUpdate(BaseModel):
    name: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    capacity_two_wheeler: int | None = None
    capacity_three_wheeler: int | None = None
    capacity_four_wheeler: int | None = None
    capacity_six_wheeler: int | None = None


class ParkingZoneOut(BaseModel):
    id: int
    name: str
    center_lat: float
    center_lng: float
    capacity_two_wheeler: int
    capacity_three_wheeler: int
    capacity_four_wheeler: int
    capacity_six_wheeler: int
    occupied_two_wheeler: int
    occupied_three_wheeler: int
    occupied_four_wheeler: int
    occupied_six_wheeler: int
    updated_at: datetime

    class Config:
        from_attributes = True


class ParkingBookingCreate(BaseModel):
    parking_zone_id: int
    vehicle_type: str
    vehicle_number: str


class ParkingBookingOut(BaseModel):
    id: int
    parking_zone_id: int
    vehicle_type: str
    vehicle_number: str
    created_at: datetime

    class Config:
        from_attributes = True
