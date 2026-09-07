from datetime import datetime

from pydantic import BaseModel


class ZoneCreate(BaseModel):
    name: str
    center_lat: float
    center_lng: float


class ZoneCrowdUpdate(BaseModel):
    crowd_level: str  # green | yellow | red


class ZoneOut(BaseModel):
    id: int
    name: str
    center_lat: float
    center_lng: float
    crowd_level: str
    updated_at: datetime

    class Config:
        from_attributes = True
