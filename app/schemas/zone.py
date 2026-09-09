from datetime import datetime

from pydantic import BaseModel


class ZoneCreate(BaseModel):
    name: str
    center_lat: float
    center_lng: float
    radius_m: float = 300.0
    crowd_level: str = "green"  # green | yellow | red


class ZoneUpdate(BaseModel):
    name: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    radius_m: float | None = None
    crowd_level: str | None = None


class ZoneCrowdUpdate(BaseModel):
    crowd_level: str  # green | yellow | red


class ZoneOut(BaseModel):
    id: int
    name: str
    center_lat: float
    center_lng: float
    radius_m: float
    crowd_level: str
    updated_at: datetime

    class Config:
        from_attributes = True
